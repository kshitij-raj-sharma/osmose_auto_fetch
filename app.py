# %%
import pandas as pd
import requests
import datetime
# %%
BASE_API_URL = "https://osmose.openstreetmap.fr/en/issues/open.json?item=xxxx"

countries = [
    "Afghanistan",
    "Bangladesh",
    "Bhutan",
    "Brunei",
    "Cambodia",
    "Micronesia",
    "Fiji",
    "India",
    "Indonesia",
    "Kiribati",
    "Laos",
    "Malaysia",
    "Myanmar",
    "Nepal",
    "Pakistan",
    "Papua New Guinea",
    "Philippines",
    "Solomon Islands",
    "Sri Lanka",
    "East Timor",
    "Tonga",
    "Turkey",
    "Syria",
    "Uzbekistan",
    "Vanuatu",
    "VietNam",
    "Yemen",
]

conflicted_countries = {}

data = []


def get_cleaned_country(countries):
    formatted_countries = []
    print("Sending Request to osmose Countries API")
    API = "https://osmose.openstreetmap.fr/api/0.3/countries"
    response = requests.get(API).json()
    countries_received = response["countries"]
    # clean bugs on osmosis api
    if "indonesia" in countries_received:
        countries_received.remove(
            "indonesia"
        )  # indonesia has bug on osmose , it has divided to sub regions yet available as single country on api
    if "india_dadra_and_nagar_haveli" in countries_received:
        countries_received.remove("india_dadra_and_nagar_haveli")
        if "india_dadra_and_nagar_haveli_and_daman_and_diu" not in countries_received:
            countries_received.append("india_dadra_and_nagar_haveli_and_daman_and_diu")
    if "india_daman_and_diu" in countries_received:
        countries_received.remove("india_daman_and_diu")
        if "india_dadra_and_nagar_haveli_and_daman_and_diu" not in countries_received:
            countries_received.append("india_dadra_and_nagar_haveli_and_daman_and_diu")
    for country in countries:
        country = country.lower().replace(" ", "_")

        if not country in countries_received:

            #    print(f"No direct match for {country} , Trying to check subdatasets")
            sub_matches = [
                cntr for cntr in countries_received if cntr.startswith(country)
            ]

            if len(sub_matches) > 0:
                formatted_countries.extend(sub_matches)
                conflicted_countries[country] = sub_matches
            else:
                print(f"Match didn't found for {country}")
        else:
            formatted_countries.append(country)
    return formatted_countries


def is_country_exists(country_name):
    API = "https://osmose.openstreetmap.fr/api/0.3/countries"
    response = requests.get(API).json()
    if country_name.lower() not in response["countries"]:
        print(f"{country_name} doesn't exists on osmose")
        return False
    return True


def fetch_country(country_name):
    country_name = country_name.lower().replace(
        " ", "_"
    )  # lower case everyname and replace spaces
    if is_country_exists(country_name):
        call_api_url = BASE_API_URL + f"&country={country_name}"
        print(f"Fetching {call_api_url}")
        response = requests.get(call_api_url)
        if response.status_code == 200:
            data.extend(response.json()["errors_groups"])
            return True
        return False


# %%
formatted_countries = get_cleaned_country(countries)
# loop through each country specified
for country in formatted_countries:
    # fetch country data
    status = fetch_country(country)
    if status is False:
        print("Error for {country}")

# Convert the collected response to a pandas DataFrame
meta_df = pd.DataFrame(data)

df = meta_df.groupby(["menu", "country"], as_index=False)["count"].sum()

pivot = df.pivot(index="menu", columns="country", values="count")

# %%

for key in conflicted_countries.keys():

    # Extract the new column name and the column names to be merged

    new_column_name = key
    columns_to_merge = conflicted_countries[key]

    # Create the new column as the sum of the specified columns
    pivot[new_column_name] = pivot[columns_to_merge].sum(axis=1)
    # Drop the merged columns
    pivot.drop(columns_to_merge, axis=1, inplace=True)

pivot["Total"] = pivot.sum(axis=1)
pivot.loc["Total"] = pivot.sum(axis=0)
pivot['Fetched_date'] = datetime.datetime.now()
# %%
print(pivot.columns.tolist())

# %%
meta_df.to_csv("data/meta.csv", index=True)
pivot.to_csv("data/summary.csv", index=True)
