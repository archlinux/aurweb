PREFIX = /usr/local

CFLAGS = -g -std=c99 -pedantic -Wall -I/usr/include/mysql
LDFLAGS = -g -lalpm -lmysqlclient

CC = cc
