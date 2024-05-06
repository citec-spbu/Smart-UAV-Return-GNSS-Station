#include <string>
#include <iostream>
#include <geomap_db.hpp>

const int EMBEDDING_DIMENSION = 3;
const std::string DATABASE_NAME = "geomap.db";
const std::string DATABASE_TABLE_NAME = "geomap_embeddings";

int main()
{
    GeomapDB geomap_db(EMBEDDING_DIMENSION, DATABASE_NAME, DATABASE_TABLE_NAME);

    geomap_db.print_db(std::cout);

    return 0;
}
