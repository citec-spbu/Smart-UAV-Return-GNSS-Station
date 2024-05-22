#include <geomap_db.hpp>
#include <iostream>

int main()
{
    GeomapDB geomap(16, "geomap.db", "geomap_embeddings");
    geomap.print_db(std::cout);
}
