#ifndef GEOMAP_DB_HPP
#define GEOMAP_DB_HPP

#include <string>
#include <vector>
#include <iostream>
#include <stdexcept>
#include <sqlite3.h>

class GeomapDB
{
public:
    GeomapDB(const unsigned, const std::string &, const std::string &);
    ~GeomapDB();

    std::ostream &print_db(std::ostream &);
    void insert(const double, const double, const std::vector<double> &);
    std::vector<std::vector<double>> get_closest(const double, const double, const double);
    std::vector<std::vector<double>> get_most_similar(const std::vector<double> &, const double);
    std::vector<std::vector<double>> get_closest_most_similar(const double, const double, const std::vector<double> &, const double, const double);

private:
    std::string db_name;
    std::string table_name;
    sqlite3 *db;
    char *err;
    sqlite3_stmt *stmt;
    unsigned embedding_dim;

    void connection();
    void create_table();
    std::vector<std::vector<double>> select(const std::string &);
    std::string get_closest_condition(const double, const double, const double);
    std::string get_most_similar_condition(const std::vector<double> &, const double);
};

#endif
