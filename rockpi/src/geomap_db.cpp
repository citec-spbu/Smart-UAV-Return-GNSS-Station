#include <geomap_db.hpp>

GeomapDB::GeomapDB(const unsigned dim_embedding, const std::string &database_name, const std::string &tbl_name = "geomap_embeddings")
{
    db_name = database_name;
    table_name = tbl_name;
    embedding_dim = dim_embedding;
    connection();
    create_table();
}

GeomapDB::~GeomapDB()
{
    int rc = sqlite3_close(db);
    if (rc != SQLITE_OK)
    {
        std::cerr << sqlite3_errmsg(db) << std::endl;
    }
}

std::ostream &GeomapDB::print_db(std::ostream &os)
{
    std::string query = "SELECT * FROM " + table_name;
    std::vector<std::vector<double>> rows = select(query);
    os << table_name << std::endl;
    for (const auto row : rows)
    {
        for (const auto element : row)
        {
            os << std::to_string(element) << "; ";
        }
        os << std::endl;
    }
    return os;
}

std::string GeomapDB::get_closest_condition(const double lat, const double lon, const double eps)
{
    std::string lat_condition = std::to_string(lat - eps) + " <= lat AND lat <= " + std::to_string(lat + eps);
    std::string lon_condition = std::to_string(lon - eps) + " <= lon AND lon <= " + std::to_string(lon + eps);
    std::string condition = lat_condition + " AND " + lon_condition;
    return condition;
}

std::string GeomapDB::get_embedding_distances_table(const std::vector<double> &embedding)
{
    if (embedding.size() != embedding_dim)
        throw std::runtime_error("Embedding must have " + std::to_string(embedding_dim) + " cords, " + std::to_string(embedding.size()) + " were given!");
    std::string condition = "SELECT *, (";
    for (int i = 0; i < embedding_dim; ++i)
    {
        condition += "ABS(embedding" + std::to_string(i) + " - " + std::to_string(embedding[i]) + ")";
        if (i < embedding_dim - 1)
            condition += " + ";
        else
            condition += ") AS embedding_distance FROM " + table_name;
    }
    return condition;
}

void GeomapDB::connection()
{
    int rc = sqlite3_open(db_name.c_str(), &db) == SQLITE_OK;
    if (rc != SQLITE_OK)
    {
        std::cerr << "Connection error: " << sqlite3_errmsg(db) << std::endl;
    }
}

void GeomapDB::create_table()
{
    std::string embedding_init = "";
    for (int i = 0; i < embedding_dim; ++i)
    {
        embedding_init += ", embedding" + std::to_string(i) + " DOUBLE";
    }
    std::string query = "CREATE TABLE IF NOT EXISTS " + table_name + "(lat DOUBLE, lon DOUBLE" + embedding_init + ");";
    int rc = sqlite3_exec(db, query.c_str(), NULL, NULL, &err);
    if (rc != SQLITE_OK)
    {
        std::cerr << "Creating table error: " << err << std::endl;
    }
}

void GeomapDB::insert(const double lat, const double lon, const std::vector<double> &embedding)
{
    std::string values = std::to_string(lat) + ", " + std::to_string(lon);
    for (const auto cord : embedding)
    {
        values += ", " + std::to_string(cord);
    }
    std::string query = "INSERT INTO " + table_name + " VALUES(" + values + ");";

    int rc = sqlite3_exec(db, query.c_str(), NULL, NULL, &err);

    if (rc != SQLITE_OK)
    {
        std::cerr << "Insertion error: " << err << std::endl;
    }
}

std::vector<std::vector<double>> GeomapDB::get_closest_objects(const double lat, const double lon, const double eps)
{
    std::string condition = get_closest_condition(lat, lon, eps);
    std::string query = "SELECT * FROM " + table_name + " WHERE " + condition + ";";
    return select(query);
}

std::vector<double> GeomapDB::get_most_similar_object(const std::vector<double> &embedding)
{
    std::string embedding_distance_table = get_embedding_distances_table(embedding);
    std::string query = "SELECT * FROM (" + embedding_distance_table + " ORDER BY embedding_distance) DESK LIMIT 1;";
    std::vector<std::vector<double>> result = select(query);
    std::cout << result.size() << std::endl;
    if (result.empty())
        return {};
    else
        return result[0];
}

std::vector<double> GeomapDB::get_closest_most_similar_object(const double lat, const double lon, const double eps_loc, const std::vector<double> &embedding)
{
    std::string condition = get_closest_condition(lat, lon, eps_loc);
    std::string embedding_distance_table = get_embedding_distances_table(embedding);
    std::string query = "SELECT * FROM (" + embedding_distance_table + " WHERE " + condition + " ORDER BY embedding_distance)" + "DESK LIMIT 1;";
    std::vector<std::vector<double>> result = select(query);
    if (result.empty())
        return {};
    else
        return result[0];
}

std::vector<double> GeomapDB::get_approximate_location(const double prev_lat, const double prev_lon, const double location_eps, const std::vector<std::vector<double>> &input_embeddings)
{
    unsigned found_matches = 0;
    double approx_lat = 0, approx_lon = 0;
    for (const auto embedding : input_embeddings)
    {
        std::vector<double> embedding_matched = get_closest_most_similar_object(prev_lat, prev_lon, location_eps, embedding);
        if (!embedding_matched.empty())
        {
            ++found_matches;
            approx_lat += embedding_matched[0];
            approx_lon += embedding_matched[1];
        }
    }
    approx_lat /= found_matches;
    approx_lon /= found_matches;
    return {approx_lat, approx_lon};
}

std::vector<std::vector<double>> GeomapDB::select(const std::string &query)
{
    int rc = sqlite3_prepare_v2(db, query.c_str(), -1, &stmt, 0);
    std::vector<std::vector<double>> result;
    if (rc != SQLITE_OK)
    {
        return result;
    }
    while (sqlite3_step(stmt) != SQLITE_DONE)
    {
        std::vector<double> row = {};
        double lat = sqlite3_column_double(stmt, 0);
        double lon = sqlite3_column_double(stmt, 1);
        row.push_back(lat);
        row.push_back(lon);
        for (int i = 2; i < embedding_dim + 2; ++i)
        {
            double embedding_cord = sqlite3_column_double(stmt, i);
            row.push_back(embedding_cord);
        }
        result.push_back(row);
    }
    sqlite3_finalize(stmt);
    return result;
}
