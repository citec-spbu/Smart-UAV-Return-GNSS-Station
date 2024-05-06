#include <string>
#include <vector>
#include <geomap_db.hpp>

const int EMBEDDING_DIMENSION = 3;
const std::string DATABASE_NAME = "geomap.db";
const std::string DATABASE_TABLE_NAME = "geomap_embeddings";

int main(int argc, char *argv[])
{
    GeomapDB geomap_db(EMBEDDING_DIMENSION, DATABASE_NAME, DATABASE_TABLE_NAME);

    const double lat = std::stod(argv[1]);
    const double lon = std::stod(argv[2]);

    std::vector<double> embedding;

    for (int i = 3; i < argc; ++i)
        embedding.push_back(std::stod(argv[i]));

    geomap_db.insert(lat, lon, embedding);

    return 0;
}
