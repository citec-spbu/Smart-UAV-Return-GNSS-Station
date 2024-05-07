#include <geomap_db.hpp>
#include <iostream>
#include <sstream>
#include <vector>

using namespace std;

int main()
{
    unsigned emb_dim = 3;
    string db_name = "geomap.db";
    string table_name = "geomap_embeddings";
    GeomapDB geomap_db(emb_dim, db_name, table_name);

    string emb;
    while (getline(cin, emb))
    {
        if (emb == "q")
            break;
        stringstream ss(emb);
        string value;
        vector<double> embedding = {};
        while (getline(ss, value, ' '))
        {
            embedding.push_back(stod(value));
        }
        cout << "Enter lat and lon:" << endl;
        double lat, lon;
        cin >> lat >> lon;
        geomap_db.insert(lat, lon, embedding);
        cin.ignore();
    }

    geomap_db.print_db(cout) << endl;

    cout << "Closest similar embeddings" << endl;
    vector<vector<double>> embeddings = {{1, 2, 3}, {2, 2, 2}, {5, 5, 1}};
    std::vector<double> approx_cords = geomap_db.get_approximate_location(30, 69, 2, embeddings);
    cout << approx_cords[0] << " " << approx_cords[1] << endl;


    return 0;
}
