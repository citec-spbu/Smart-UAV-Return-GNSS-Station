#include <location_seeker.hpp>

std::vector<std::vector<double>> LocationSeeker::get_image_embeddings(const std::string &image_path)
{
    py::module_ image_processing = py::module_::import("py_src.image_processing");
    py::object image_embeddings = image_processing.attr("get_geomap_embeddings")(image_path);
    std::vector<std::vector<double>> result(image_embeddings.cast<std::vector<std::vector<double>>>());
    std::cout << "Detected " << result.size() << " objects" << std::endl;
    return result;
}

std::vector<double> LocationSeeker::update_current_location(const std::string &image_path, const double eps)
{
    std::vector<std::vector<double>> image_embeddings = get_image_embeddings(image_path);
    double temp_lat = 0, temp_lon = 0;
    unsigned recognition_amount = 0;
    for (const auto img_embed : image_embeddings)
    {
        std::vector<double> db_embedding(geomap_db.get_closest_most_similar_object(previous_lon, previous_lat, eps, img_embed));
        if (!db_embedding.empty())
        {
            recognition_amount += 1;
            temp_lat += db_embedding[0];
            temp_lon += db_embedding[1];
        }
    }
    std::cout << "Recognized " << recognition_amount << " objects" << std::endl;
    if (recognition_amount)
    {
        previous_lat = temp_lat / recognition_amount;
        previous_lon = temp_lon / recognition_amount;
    }
    return {previous_lat, previous_lon};
}
