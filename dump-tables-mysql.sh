#!/bin/bash

# dump-tables-mysql.sh
# Descr: Dump MySQL table data into separate SQL files for a specified database.
# Usage: Run without args for usage info.
# Author: @Trutane
# Ref: http://stackoverflow.com/q/3669121/138325
# Notes:
#  * Script will prompt for password for db access.
#  * Output files are compressed and saved in the current working dir, unless DIR is
#    specified on command-line.

[ $# -lt 3 ] && echo "Usage: $(basename $0) <DB_HOST> <DB_USER> <DB_PASSWORD> <DB_NAME> [<DIR>]" && exit 1

DB_host=$1
DB_user=$2
DB_pass=$3
DB=$4
DIR=$5

[ -n "$DIR" ] || DIR=.
test -d $DIR || mkdir -p $DIR

# echo -n "DB password: "
# read -s DB_pass
echo
echo "Dumping tables into separate SQL command files for database '$DB' into dir=$DIR"

tbl_count=0

for t in $(mysql -NBA -h $DB_host -u $DB_user -p$DB_pass -D $DB -e 'show tables')
do
    echo "DUMPING TABLE: $DB.$t"
    mysqldump --no-tablespaces --column-statistics=0 -h $DB_host -u $DB_user -p$DB_pass $DB $t | gzip > $DIR/$DB.$t.sql.gz
    tbl_count=$(( tbl_count + 1 ))
done

echo "$tbl_count tables dumped from database '$DB' into dir=$DIR"
