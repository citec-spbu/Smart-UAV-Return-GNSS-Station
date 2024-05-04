#include <geomap_db.hpp>

GeomapDB::GeomapDB(const std::string &database_name, const unsigned dim_embedding)
{
    db_name = database_name;
    embedding_dim = dim_embedding;
    connection();
    create_table();
}

GeomapDB::~GeomapDB()
{
    sqlite3_finalize(stmt);
    int rc = sqlite3_close(db);
    if (rc != SQLITE_OK)
    {
        std::cerr << sqlite3_errmsg(db) << std::endl;
    }
}

void GeomapDB::insert_embedding(const std::vector<double> &embedding, const double lat, const double lon)
{
    if (embedding.size() != embedding_dim) {
        throw std::runtime_error("Embedding must have " + std::to_string(embedding_dim) + " cords, " + std::to_string(embedding.size()) + " were given!");
    }
    std::string embedding_str = "";
    for (const auto embedding_cord : embedding)
    {
        embedding_str += std::to_string(embedding_cord) + ";";
    }
    insert(embedding_str, lat, lon);
}

std::vector<std::vector<double>> GeomapDB::get_closest(const double lat, const double lon, const double eps)
{
    std::string lat_condition = std::to_string(lat - eps) + " <= lat AND lat <= " + std::to_string(lat + eps);
    std::string lon_condition = std::to_string(lon - eps) + " <= lon AND lon <= " + std::to_string(lon + eps);
    std::string query = "SELECT embedding, lat, lon FROM geomap_embeddings WHERE " + lat_condition + " AND " + lon_condition + ";";
    std::vector<std::vector<double>> res = select(query);
    return res;
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
    int rc = sqlite3_exec(db, "CREATE TABLE IF NOT EXISTS geomap_embeddings(embedding TEXT, lat DOUBLE, lon DOUBLE);", NULL, NULL, &err);
    if (rc != SQLITE_OK)
    {
        std::cerr << "Creating table error: " << err << std::endl;
    }
}

void GeomapDB::insert(const std::string &embedding, const double lat, const double lon)
{
    std::string values = "('" + embedding + "', " + std::to_string(lat) + ", " + std::to_string(lon) + ")";
    std::string query = "INSERT INTO geomap_embeddings VALUES " + values + ";";

    int rc = sqlite3_exec(db, query.c_str(), NULL, NULL, &err);

    if (rc != SQLITE_OK)
    {
        std::cerr << "Insertion error: " << err << std::endl;
    }
}

std::vector<std::vector<double>> GeomapDB::select(const std::string &query)
{
    sqlite3_prepare_v2(db, query.c_str(), -1, &stmt, 0);
    std::vector<std::vector<double>> result;
    std::vector<double> row;
    while (sqlite3_step(stmt) != SQLITE_DONE)
    {
        std::string embedding = reinterpret_cast<char const *>(sqlite3_column_text(stmt, 0));
        std::stringstream ss(embedding);
        std::string embedding_cord;
        while (std::getline(ss, embedding_cord, ';'))
        {
            row.push_back(stod(embedding_cord));
        }
        double lat = sqlite3_column_double(stmt, 1);
        double lon = sqlite3_column_double(stmt, 2);
        row.push_back(lat);
        row.push_back(lon);
        result.push_back(row);
        row.clear();
    }
    return result;
}
