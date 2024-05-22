#ifndef LOCATION_SEEKER_HPP
#define LOCATION_SEEKER_HPP

#include <string>
#include <vector>
#include <iostream>
#include <geomap_db.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/embed.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class LocationSeeker
{
public:
    LocationSeeker(const unsigned emb_dim, const std::string &geomap_db_name, const double prev_lon, const double prev_lat) : geomap_db(emb_dim, geomap_db_name, "geomap_embeddings"), previous_lon(prev_lon), previous_lat(prev_lat) {};
    std::vector<double> update_current_location(const std::string &, const double);

private:
    py::scoped_interpreter guard{};
    GeomapDB geomap_db;
    unsigned embedding_dim;
    double previous_lon, previous_lat;

    std::vector<std::vector<double>> get_image_embeddings(const std::string &);
};

#endif
