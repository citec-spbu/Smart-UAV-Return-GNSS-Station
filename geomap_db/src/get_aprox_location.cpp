#include <location_seeker.hpp>
#include <string>
#include <vector>
#include <iostream>
#include <stdexcept>

const unsigned EMBEDDING_DIMENSION = 16;
const double LOCATION_EPS = 0.001;

int main(int argc, char *argv[])
{
    if (argc != 4)
        throw std::runtime_error("Input must be in form of (uav_input lon lat)");
    std::string uav_input = argv[1];
    double prev_lon = std::stod(argv[2]), prev_lat = std::stod(argv[3]);
    LocationSeeker lock_seeker(EMBEDDING_DIMENSION, "geomap.db", prev_lon, prev_lat);
    std::cout << uav_input << std::endl;
    std::vector<double> new_cords = lock_seeker.update_current_location(uav_input, LOCATION_EPS);
    prev_lon = new_cords[0];
    prev_lat = new_cords[1];
    std::cout << prev_lon << " " << prev_lat << std::endl;
    return 0;
}
