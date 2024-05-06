#include <string>
#include <vector>
#include <set>
#include <geomap_db.hpp>

const int EMBEDDING_DIMENSION = 3;
const std::string DATABASE_NAME = "geomap.db";
const std::string DATABASE_TABLE_NAME = "geomap_embeddings";

const double POSITION_EPS = 1; // Better to be set more than 2*<UAV-velocity>*<delta-time>
const double EMBEDDING_EPS = 1;

int main(int argc, char *argv[])
{
    GeomapDB geomap_db(EMBEDDING_DIMENSION, DATABASE_NAME, DATABASE_TABLE_NAME);

    const double prev_lat = std::stod(argv[1]);
    const double prev_lon = std::stod(argv[2]);

    unsigned embeddings_amount = (argc - 3) / EMBEDDING_DIMENSION;

    std::vector<std::vector<double>> embeddings;
    std::vector<std::vector<double>> nearest_similar_objects;


    for (int i = 0; i < embeddings_amount; ++i)
    {
        std::vector<double> embedding = {};
        for (int j = 0; j < EMBEDDING_DIMENSION; ++j)
        {
            embedding.push_back(std::stod(argv[3 + i * EMBEDDING_DIMENSION + j]));
        }
        embeddings.push_back(embedding);
        nearest_similar_objects = geomap_db.get_closest_most_similar(prev_lat, prev_lon, embedding, POSITION_EPS, EMBEDDING_EPS);
    }

    

    return 0;
}
