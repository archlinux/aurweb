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

#define alpm_die(...) die(__VA_ARGS__, alpm_strerrorlast());
#define mysql_die(...) die(__VA_ARGS__, mysql_error(c));

void die(const char *, ...);
alpm_list_t *pkglist_append(alpm_list_t *, const char *);
alpm_list_t *blacklist_get_pkglist();
void blacklist_add(const char *);
void blacklist_remove(const char *);
void blacklist_sync(alpm_list_t *, alpm_list_t *);
alpm_list_t *dblist_get_pkglist(alpm_list_t *);
alpm_list_t *dblist_create(void);
void read_config(const char *);
void init(void);
void cleanup(void);

static char *mysql_host = NULL;
static char *mysql_socket = NULL;
static char *mysql_user = NULL;
static char *mysql_passwd = NULL;
static char *mysql_db = NULL;

MYSQL *c;

void
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

alpm_list_t *
pkglist_append(alpm_list_t *pkglist, const char *pkgname)
{
  int len = strcspn(pkgname, "<=>");
  if (!len) len = strlen(pkgname);

  char *s = malloc(len + 1);

  strncpy(s, pkgname, len);
  s[len] = 0;

  if (alpm_list_find_str(pkglist, s))
    free(s);
  else
    pkglist = alpm_list_add(pkglist, s);

  return pkglist;
}

alpm_list_t *
blacklist_get_pkglist()
{
  MYSQL_RES *res;
  MYSQL_ROW row;
  alpm_list_t *pkglist = NULL;

  if (mysql_query(c, "SELECT Name FROM PackageBlacklist;"))
    mysql_die("failed to read blacklist from MySQL database: %s\n");

  if (!(res = mysql_store_result(c)))
    mysql_die("failed to store MySQL result: %s\n");

  while ((row = mysql_fetch_row(res)))
    pkglist = pkglist_append(pkglist, row[0]);

  mysql_free_result(res);

  return pkglist;
}

void
blacklist_add(const char *name)
{
  char *esc = malloc(strlen(name) * 2 + 1);
  char query[1024];

  mysql_real_escape_string(c, esc, name, strlen(name));
  snprintf(query, 1024, "INSERT INTO PackageBlacklist (Name) "
                        "VALUES ('%s');", esc);
  free(esc);

  if (mysql_query(c, query))
    mysql_die("failed to query MySQL database (\"%s\"): %s\n", query);
}

void
blacklist_remove(const char *name)
{
  char *esc = malloc(strlen(name) * 2 + 1);
  char query[1024];

  mysql_real_escape_string(c, esc, name, strlen(name));
  snprintf(query, 1024, "DELETE FROM PackageBlacklist WHERE Name = '%s';", esc);
  free(esc);

  if (mysql_query(c, query))
    mysql_die("failed to query MySQL database (\"%s\"): %s\n", query);
}

void
blacklist_sync(alpm_list_t *pkgs_cur, alpm_list_t *pkgs_new)
{
  alpm_list_t *pkgs_add, *pkgs_rem, *p;

#if MYSQL_USE_TRANSACTIONS
  if (mysql_autocommit(c, 0))
    mysql_die("failed to turn MySQL autocommit off: %s\n");

  if (mysql_query(c, "START TRANSACTION;"))
    mysql_die("failed to start MySQL transaction: %s\n");
#else
  if (mysql_query(c, "LOCK TABLES PackageBlacklist WRITE;"))
    mysql_die("failed to lock MySQL table: %s\n");
#endif

  pkgs_add = alpm_list_diff(pkgs_new, pkgs_cur, (alpm_list_fn_cmp)strcmp);
  pkgs_rem = alpm_list_diff(pkgs_cur, pkgs_new, (alpm_list_fn_cmp)strcmp);

  for (p = pkgs_add; p; p = alpm_list_next(p))
    blacklist_add(alpm_list_getdata(p));

  for (p = pkgs_rem; p; p = alpm_list_next(p))
    blacklist_remove(alpm_list_getdata(p));

  alpm_list_free(pkgs_add);
  alpm_list_free(pkgs_rem);

#if MYSQL_USE_TRANSACTIONS
  if (mysql_query(c, "COMMIT;"))
    mysql_die("failed to commit MySQL transaction: %s\n");
#else
  if (mysql_query(c, "UNLOCK TABLES;"))
    mysql_die("failed to unlock MySQL tables: %s\n");
#endif
}

alpm_list_t *
dblist_get_pkglist(alpm_list_t *dblist)
{
  alpm_list_t *d, *p, *q;
  alpm_list_t *pkglist = NULL;

  for (d = dblist; d; d = alpm_list_next(d)) {
    pmdb_t *db = alpm_list_getdata(d);

    if (alpm_trans_init(0, NULL, NULL, NULL))
      alpm_die("failed to initialize ALPM transaction: %s\n");
    if (alpm_db_update(0, db) < 0)
      alpm_die("failed to update ALPM database: %s\n");
    if (alpm_trans_release())
      alpm_die("failed to release ALPM transaction: %s\n");

    for (p = alpm_db_get_pkgcache(db); p; p = alpm_list_next(p)) {
      pmpkg_t *pkg = alpm_list_getdata(p);

      pkglist = pkglist_append(pkglist, alpm_pkg_get_name(pkg));

      for (q = alpm_pkg_get_provides(pkg); q; q = alpm_list_next(q))
        pkglist = pkglist_append(pkglist, alpm_list_getdata(q));

      for (q = alpm_pkg_get_replaces(pkg); q; q = alpm_list_next(q))
        pkglist = pkglist_append(pkglist, alpm_list_getdata(q));
    }
  }

  return pkglist;
}

alpm_list_t *
dblist_create(void)
{
  alpm_list_t *d;
  alpm_list_t *dblist = NULL;
  int i;

  for (i = 0; i < sizeof(alpm_repos) / sizeof(char *); i++) {
    if (!alpm_db_register_sync(alpm_repos[i]))
      alpm_die("failed to register sync db \"%s\": %s\n", alpm_repos[i]);
  }

  if (!(dblist = alpm_option_get_syncdbs()))
    alpm_die("failed to get sync DBs: %s\n");

  for (d = dblist; d; d = alpm_list_next(d)) {
    pmdb_t *db = alpm_list_getdata(d);

    char server[1024];
    snprintf(server, 1024, ALPM_MIRROR, alpm_db_get_name(db));

    if (alpm_db_setserver(db, server))
      alpm_die("failed to set server \"%s\": %s\n", server);
  }

  return dblist;
}

void
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
    else if (strstr(line, CONFIG_KEY_USER)) t = &mysql_user;
    else if (strstr(line, CONFIG_KEY_PASSWD)) t = &mysql_passwd;
    else if (strstr(line, CONFIG_KEY_DB)) t = &mysql_db;
    else t = NULL;

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

void
init(void)
{
  if (mysql_library_init(0, NULL, NULL))
    mysql_die("could not initialize MySQL library: %s\n");
  if (!(c = mysql_init(NULL)))
    mysql_die("failed to setup MySQL client: %s\n");
  if (!mysql_real_connect(c, mysql_host, mysql_user, mysql_passwd,
                          mysql_db, 0, mysql_socket, 0))
    mysql_die("failed to initiate MySQL connection to %s: %s\n", mysql_host);

  if (alpm_initialize())
    alpm_die("failed to initialize ALPM: %s\n");
  if (alpm_option_set_root("/"))
    alpm_die("failed to set ALPM root: %s\n");
  if (alpm_option_set_dbpath(ALPM_DBPATH))
    alpm_die("failed to set ALPM database path: %s\n");
}

void
cleanup(void)
{
  if (mysql_host) free(mysql_host);
  if (mysql_socket) free(mysql_socket);
  if (mysql_user) free(mysql_user);
  if (mysql_passwd) free(mysql_passwd);
  if (mysql_db) free(mysql_db);

  alpm_release();
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
