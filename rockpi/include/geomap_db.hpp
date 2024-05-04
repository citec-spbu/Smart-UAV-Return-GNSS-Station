#ifndef GEOMAP_DB_HPP
#define GEOMAP_DB_HPP

#include <string>
#include <sstream>
#include <vector>
#include <iostream>
#include <stdexcept>
#include <sqlite3.h>

class GeomapDB
{
public:
    GeomapDB(const std::string &, const unsigned);
    ~GeomapDB();

    void insert_embedding(const std::vector<double> &, const double, const double);
    std::vector<std::vector<double>> get_closest(const double, const double, const double);

private:
    std::string db_name;
    sqlite3 *db;
    char *err;
    sqlite3_stmt *stmt;
    unsigned embedding_dim;

    void connection();
    void create_table();
    void insert(const std::string &, const double, const double);
    std::vector<std::vector<double>> select(const std::string &);
};

#endif
