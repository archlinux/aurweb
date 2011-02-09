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
void blacklist_add(const char *);
void blacklist_sync(alpm_list_t *);
alpm_list_t *get_package_list(alpm_list_t *);
alpm_list_t *create_db_list(void);
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

void
blacklist_add(const char *name)
{
  char *esc = malloc(strlen(name) * 2 + 1);
  char query[1024];

  mysql_real_escape_string(c, esc, name, strlen(name));
  *(esc + strcspn(esc, "<=>")) = 0;
  snprintf(query, 1024, "INSERT IGNORE INTO PackageBlacklist (Name) "
                        "VALUES ('%s');", esc);
  free(esc);

  if (mysql_query(c, query))
    mysql_die("failed to query MySQL database (\"%s\"): %s\n", query);
}

void
blacklist_sync(alpm_list_t *pkgs)
{
  alpm_list_t *r, *p;

  if (mysql_query(c, "LOCK TABLES PackageBlacklist WRITE;"))
    mysql_die("failed to lock MySQL table: %s\n");

  if (mysql_query(c, "DELETE FROM PackageBlacklist;"))
    mysql_die("failed to clear MySQL table: %s\n");

  for (r = pkgs; r; r = alpm_list_next(r)) {
    pmpkg_t *pkg = alpm_list_getdata(r);

    blacklist_add(alpm_pkg_get_name(pkg));

    for (p = alpm_pkg_get_provides(pkg); p; p = alpm_list_next(p)) {
      blacklist_add(alpm_list_getdata(p));
    }

    for (p = alpm_pkg_get_replaces(pkg); p; p = alpm_list_next(p)) {
      blacklist_add(alpm_list_getdata(p));
    }
  }

  if (mysql_query(c, "UNLOCK TABLES;"))
    mysql_die("failed to unlock MySQL tables: %s\n");
}

alpm_list_t *
get_package_list(alpm_list_t *dblist)
{
  alpm_list_t *r, *pkgs = NULL;

  for (r = dblist; r; r = alpm_list_next(r)) {
    pmdb_t *db = alpm_list_getdata(r);

    if (alpm_trans_init(0, NULL, NULL, NULL))
      alpm_die("failed to initialize ALPM transaction: %s\n");
    if (alpm_db_update(0, db) < 0)
      alpm_die("failed to update ALPM database: %s\n");
    if (alpm_trans_release())
      alpm_die("failed to release ALPM transaction: %s\n");

    pkgs = alpm_list_join(pkgs, alpm_list_copy(alpm_db_get_pkgcache(db)));
  }

  return pkgs;
}

alpm_list_t *
create_db_list(void)
{
  alpm_list_t *r, *dblist = NULL;
  int i;

  for (i = 0; i < sizeof(alpm_repos) / sizeof(char *); i++) {
    if (!alpm_db_register_sync(alpm_repos[i]))
      alpm_die("failed to register sync db \"%s\": %s\n", alpm_repos[i]);
  }

  if (!(dblist = alpm_option_get_syncdbs()))
    alpm_die("failed to get sync DBs: %s\n");

  for (r = dblist; r; r = alpm_list_next(r)) {
    pmdb_t *db = alpm_list_getdata(r);

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
  alpm_list_t *pkgs;

  read_config(AUR_CONFIG);
  init();
  pkgs = get_package_list(create_db_list());
  blacklist_sync(pkgs);
  alpm_list_free(pkgs);
  cleanup();

  return 0;
}
