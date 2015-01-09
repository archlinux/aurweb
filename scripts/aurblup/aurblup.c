/* aurblup - AUR blacklist updater
 *
 * Small utility to update the AUR package blacklist. Can be used in a cronjob.
 * Check the "README" file for details.
 */

#include <alpm.h>
#include <getopt.h>
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
static int parse_options(int, char **);
static void init(void);
static void cleanup(void);

static char *mysql_host = "localhost";
static char *mysql_socket = NULL;
static char *mysql_user = "aur";
static char *mysql_passwd = "aur";
static char *mysql_db = "AUR";

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
    if (!alpm_register_syncdb(handle, alpm_repos[i], 0))
      alpm_die("failed to register sync db \"%s\": %s\n", alpm_repos[i]);
  }

  if (!(dblist = alpm_get_syncdbs(handle)))
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

static int parse_options(int argc, char **argv)
{
  int opt;

  static const struct option opts[] = {
    { "mysql-host",   required_argument, 0, 'h' },
    { "mysql-socket", required_argument, 0, 'S' },
    { "mysql-user",   required_argument, 0, 'u' },
    { "mysql-passwd", required_argument, 0, 'p' },
    { "mysql-db",     required_argument, 0, 'D' },
    { 0, 0, 0, 0 }
  };

  while((opt = getopt_long(argc, argv, "h:S:u:p:D:", opts, NULL)) != -1) {
    switch(opt) {
      case 'h':
        mysql_host = optarg;
        break;;
      case 'S':
        mysql_socket = optarg;
        break;;
      case 'u':
        mysql_user = optarg;
        break;;
      case 'p':
        mysql_passwd = optarg;
        break;;
      case 'D':
        mysql_db = optarg;
        break;;
      default:
        return 0;
    }
  }

  return 1;
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
  alpm_release(handle);
  mysql_close(c);
  mysql_library_end();
}

int main(int argc, char *argv[])
{
  alpm_list_t *pkgs_cur, *pkgs_new;

  if (!parse_options(argc, argv))
    return 1;

  init();

  pkgs_cur = blacklist_get_pkglist();
  pkgs_new = dblist_get_pkglist(dblist_create());
  blacklist_sync(pkgs_cur, pkgs_new);
  FREELIST(pkgs_new);
  FREELIST(pkgs_cur);

  cleanup();

  return 0;
}
