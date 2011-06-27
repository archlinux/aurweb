PREFIX = /usr/local

CFLAGS = -g -O2 -std=c99 -pedantic -Wall -I/usr/include/mysql
LDFLAGS = -g -lalpm -lmysqlclient

CC = cc
