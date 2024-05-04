#include <geomap_db.hpp>
#include <iostream>
#include <sstream>
#include <vector>

using namespace std;

int main()
{
    unsigned emb_dim;
    string db_name;
    cout << "Enter your embedding dimension configuration" << endl;
    cin >> emb_dim;
    cout << "Enter desirable name of database or the name of existing one" << endl;
    cin >> db_name;
    GeomapDB geomap_db(db_name, emb_dim);

    string emb;
    cin.ignore();
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
        geomap_db.insert_embedding(embedding, lat, lon);
        cin.ignore();
    }
    vector<vector<double>> closest_emb = geomap_db.get_closest(71, 30, 0.5);
    for (const auto row : closest_emb)
    {
        for (const auto el : row)
        {
            cout << el << " ";
        }
        cout << endl;
    }
}
