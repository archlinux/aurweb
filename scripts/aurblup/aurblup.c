/* aurblup - AUR blacklist updater
 *
 * Small utility to update the AUR package blacklist. Can be used in a cronjob.
 * Check the "README" file for details.
 */

#include <alpm.h>
#include <mysql.h>
#include <stdio.h>
#include <string.h>

#include "config.h"

#define alpm_die(...) die(__VA_ARGS__, alpm_strerror(alpm_errno(handle)));
#define mysql_die(...) die(__VA_ARGS__, mysql_error(c));

static void die(const char *, ...);
static alpm_list_t *pkglist_append(alpm_list_t *, const char *);
static alpm_list_t *blacklist_get_pkglist();
static void blacklist_add(const char *);
static void blacklist_remove(const char *);
static void blacklist_sync(alpm_list_t *, alpm_list_t *);
static alpm_list_t *dblist_get_pkglist(alpm_list_t *);
static alpm_list_t *dblist_create(void);
static void read_config(const char *);
static void init(void);
static void cleanup(void);

static char *mysql_host = NULL;
static char *mysql_socket = NULL;
static char *mysql_user = NULL;
static char *mysql_passwd = NULL;
static char *mysql_db = NULL;

static MYSQL *c;

static alpm_handle_t *handle;

static void
die(const char *format, ...)
{
  va_list arg;

  va_start(arg, format);
  fprintf(stderr, "aurblup: ");
  vfprintf(stderr, format, arg);
  va_end(arg);

  cleanup();
  exit(1);
}

static alpm_list_t *
pkglist_append(alpm_list_t *pkglist, const char *pkgname)
{
  int len = strcspn(pkgname, "<=>");
  if (!len)
    len = strlen(pkgname);

  char *s = malloc(len + 1);

  strncpy(s, pkgname, len);
  s[len] = '\0';

  if (alpm_list_find_str(pkglist, s))
    free(s);
  else
    pkglist = alpm_list_add(pkglist, s);

  return pkglist;
}

static alpm_list_t *
blacklist_get_pkglist()
{
  MYSQL_RES *res;
  MYSQL_ROW row;
  alpm_list_t *pkglist = NULL;

  if (mysql_query(c, "SELECT Name FROM PackageBlacklist"))
    mysql_die("failed to read blacklist from MySQL database: %s\n");

  if (!(res = mysql_store_result(c)))
    mysql_die("failed to store MySQL result: %s\n");

  while ((row = mysql_fetch_row(res)))
    pkglist = pkglist_append(pkglist, row[0]);

  mysql_free_result(res);

  return pkglist;
}

static void
blacklist_add(const char *name)
{
  char *esc = malloc(strlen(name) * 2 + 1);
  char query[1024];

  mysql_real_escape_string(c, esc, name, strlen(name));
  snprintf(query, 1024, "INSERT INTO PackageBlacklist (Name) "
                        "VALUES ('%s')", esc);
  free(esc);

  if (mysql_query(c, query))
    mysql_die("failed to query MySQL database (\"%s\"): %s\n", query);
}

static void
blacklist_remove(const char *name)
{
  char *esc = malloc(strlen(name) * 2 + 1);
  char query[1024];

  mysql_real_escape_string(c, esc, name, strlen(name));
  snprintf(query, 1024, "DELETE FROM PackageBlacklist WHERE Name = '%s'", esc);
  free(esc);

  if (mysql_query(c, query))
    mysql_die("failed to query MySQL database (\"%s\"): %s\n", query);
}

static void
blacklist_sync(alpm_list_t *pkgs_cur, alpm_list_t *pkgs_new)
{
  alpm_list_t *pkgs_add, *pkgs_rem, *p;

  pkgs_add = alpm_list_diff(pkgs_new, pkgs_cur, (alpm_list_fn_cmp)strcmp);
  pkgs_rem = alpm_list_diff(pkgs_cur, pkgs_new, (alpm_list_fn_cmp)strcmp);

  if (mysql_query(c, "START TRANSACTION"))
    mysql_die("failed to start MySQL transaction: %s\n");

  for (p = pkgs_add; p; p = alpm_list_next(p))
    blacklist_add(p->data);

  for (p = pkgs_rem; p; p = alpm_list_next(p))
    blacklist_remove(p->data);

  if (mysql_query(c, "COMMIT"))
    mysql_die("failed to commit MySQL transaction: %s\n");

  alpm_list_free(pkgs_add);
  alpm_list_free(pkgs_rem);
}

static alpm_list_t *
dblist_get_pkglist(alpm_list_t *dblist)
{
  alpm_list_t *d, *p, *q;
  alpm_list_t *pkglist = NULL;

  for (d = dblist; d; d = alpm_list_next(d)) {
    alpm_db_t *db = d->data;

    if (alpm_trans_init(handle, 0))
      alpm_die("failed to initialize ALPM transaction: %s\n");
    if (alpm_db_update(0, db) < 0)
      alpm_die("failed to update ALPM database: %s\n");
    if (alpm_trans_release(handle))
      alpm_die("failed to release ALPM transaction: %s\n");

    for (p = alpm_db_get_pkgcache(db); p; p = alpm_list_next(p)) {
      alpm_pkg_t *pkg = p->data;

      pkglist = pkglist_append(pkglist, alpm_pkg_get_name(pkg));

      for (q = alpm_pkg_get_provides(pkg); q; q = alpm_list_next(q)) {
        alpm_depend_t *provide = q->data;
        pkglist = pkglist_append(pkglist, provide->name);
      }

      for (q = alpm_pkg_get_replaces(pkg); q; q = alpm_list_next(q)) {
        alpm_depend_t *replace = q->data;
        pkglist = pkglist_append(pkglist, replace->name);
      }
    }
  }

  return pkglist;
}

static alpm_list_t *
dblist_create(void)
{
  alpm_list_t *d;
  alpm_list_t *dblist = NULL;
  int i;

  for (i = 0; i < sizeof(alpm_repos) / sizeof(char *); i++) {
    if (!alpm_db_register_sync(handle, alpm_repos[i], 0))
      alpm_die("failed to register sync db \"%s\": %s\n", alpm_repos[i]);
  }

  if (!(dblist = alpm_option_get_syncdbs(handle)))
    alpm_die("failed to get sync DBs: %s\n");

  for (d = dblist; d; d = alpm_list_next(d)) {
    alpm_db_t *db = d->data;

    char server[1024];
    snprintf(server, 1024, ALPM_MIRROR, alpm_db_get_name(db));

    if (alpm_db_add_server(db, server))
      alpm_die("failed to set server \"%s\": %s\n", server);
  }

  return dblist;
}

static void
read_config(const char *fn)
{
  FILE *fp;
  char line[128];
  char **t, **u, *p, *q;

  if (!(fp = fopen(fn, "r")))
    die("failed to open AUR config file (\"%s\")\n", fn);

  while (fgets(line, sizeof(line), fp)) {
    u = NULL;
    if (strstr(line, CONFIG_KEY_HOST)) {
      t = &mysql_host;
      u = &mysql_socket;
    }
    else if (strstr(line, CONFIG_KEY_USER))
      t = &mysql_user;
    else if (strstr(line, CONFIG_KEY_PASSWD))
      t = &mysql_passwd;
    else if (strstr(line, CONFIG_KEY_DB))
      t = &mysql_db;
    else
      t = NULL;

    if (t) {
      strtok(line, "\"");
      strtok(NULL, "\"");
      strtok(NULL, "\"");
      p = strtok(NULL, "\"");

      if (u) {
        p = strtok(p, ":");
        q = strtok(NULL, ":");
      }
      else q = NULL;

      if (p && !*t) {
        *t = malloc(strlen(p) + 1);
        strncpy(*t, p, strlen(p) + 1);
      }

      if (q && !*u) {
        *u = malloc(strlen(q) + 1);
        strncpy(*u, q, strlen(q) + 1);
      }
    }
  }

  fclose(fp);

  if (!mysql_host)
    die("MySQL host setting not found in AUR config file\n");
  if (!mysql_user)
    die("MySQL user setting not found in AUR config file\n");
  if (!mysql_passwd)
    die("MySQL password setting not found in AUR config file\n");
  if (!mysql_db)
    die("MySQL database setting not found in AUR config file\n");
}

static void
init(void)
{
  enum _alpm_errno_t alpm_err;
  if (mysql_library_init(0, NULL, NULL))
    mysql_die("could not initialize MySQL library: %s\n");
  if (!(c = mysql_init(NULL)))
    mysql_die("failed to setup MySQL client: %s\n");
  if (!mysql_real_connect(c, mysql_host, mysql_user, mysql_passwd,
                          mysql_db, 0, mysql_socket, 0))
    mysql_die("failed to initiate MySQL connection to %s: %s\n", mysql_host);

  if ((handle = alpm_initialize("/", ALPM_DBPATH, &alpm_err)) == NULL)
    die("failed to initialize ALPM: %s\n", alpm_strerror(alpm_err));
}

static void
cleanup(void)
{
  free(mysql_host);
  free(mysql_socket);
  free(mysql_user);
  free(mysql_passwd);
  free(mysql_db);

  alpm_release(handle);
  mysql_close(c);
  mysql_library_end();
}

int main(int argc, char *argv[])
{
  alpm_list_t *pkgs_cur, *pkgs_new;

  read_config(AUR_CONFIG);
  init();

  pkgs_cur = blacklist_get_pkglist();
  pkgs_new = dblist_get_pkglist(dblist_create());
  blacklist_sync(pkgs_cur, pkgs_new);
  FREELIST(pkgs_new);
  FREELIST(pkgs_cur);

  cleanup();

  return 0;
}
