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
    vector<double> embedding = {1, 2, 3};
    vector<vector<double>> closest_emb = geomap_db.get_closest_most_similar(71, 30, embedding, 10, 10);
    for (const auto row : closest_emb)
    {
        for (const auto el : row)
        {
            cout << el << " ";
        }
        cout << endl;
    }
    return 0;
}
