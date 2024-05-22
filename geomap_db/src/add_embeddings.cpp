#include <vector>
#include <stdexcept>
#include <geomap_db.hpp>


int main(int argc, char *argv[])
{
    const unsigned EMBEDDING_DIMENSIONS = std::stoi(argv[1]);
    if ((argc - 2) % (EMBEDDING_DIMENSIONS + 2) != 0)
        throw std::runtime_error("Something is wrong with the input!");

    unsigned embeddings_count = (argc - 2) / (EMBEDDING_DIMENSIONS + 2);

    GeomapDB geomap(EMBEDDING_DIMENSIONS, "geomap.db", "geomap_embeddings");

    for (int i = 0; i < embeddings_count; ++i)
    {
        double emb_lon = std::stod(argv[2 + (EMBEDDING_DIMENSIONS + 2) * i]);
        double emb_lat = std::stod(argv[2 + (EMBEDDING_DIMENSIONS + 2) * i + 1]);
        std::vector<double> embedding = {};
        for (int j = 2; j < EMBEDDING_DIMENSIONS + 2; ++j)
        {
            double emb_cord = std::stod(argv[2 + (EMBEDDING_DIMENSIONS + 2) * i + j]);
            embedding.push_back(emb_cord);
        }
        geomap.insert(emb_lon, emb_lat, embedding);
    }

    return 0;
}
