from fastapi import FastAPI,Query
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_groq import ChatGroq
from tavily import TavilyClient
import mysql.connector
import requests
import os
from dotenv import load_dotenv

import mysql.connector
import requests
load_dotenv()
app=FastAPI()

con=mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    port=int(os.getenv("DB_PORT")),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor = con.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS travel_details(
    id INT PRIMARY KEY AUTO_INCREMENT,
    source_city VARCHAR(100),
    destination_city VARCHAR(100),
    flight_price INT,
    hotel_price INT,
    food_price INT,
    local_transport_price INT
)
""")
cursor.execute("SELECT COUNT(*) FROM travel_details")
count = cursor.fetchone()[0]

if count == 0:
    cursor.execute("""
    INSERT INTO travel_details
    (source_city,destination_city,flight_price,hotel_price,food_price,local_transport_price)
    VALUES
    ('Hyderabad','Kochi',4500,2500,800,1000),
    ('Hyderabad','Munnar',5000,3000,900,1200),
    ('Bangalore','Kochi',3000,2500,800,1000),
     ('Bangalore','Munnar',3500,3000,900,1200),
('Bangalore','Alleppey',3700,2800,850,1100),
('Bangalore','Thekkady',4000,3500,1000,1500),
('Bangalore','Kovalam',4300,4000,1200,1800),

('Chennai','Kochi',2800,2500,800,1000),
('Chennai','Munnar',3200,3000,900,1200),
('Chennai','Alleppey',3400,2800,850,1100),
('Chennai','Thekkady',3700,3500,1000,1500),
('Chennai','Kovalam',4000,4000,1200,1800),

('Mumbai','Kochi',7000,2500,800,1000),
('Mumbai','Munnar',7500,3000,900,1200),
('Mumbai','Alleppey',7700,2800,850,1100),
('Mumbai','Thekkady',8000,3500,1000,1500),
('Mumbai','Kovalam',8300,4000,1200,1800),

('Delhi','Kochi',9000,2500,800,1000),
('Delhi','Munnar',9500,3000,900,1200),
('Delhi','Alleppey',9800,2800,850,1100),
('Delhi','Thekkady',10000,3500,1000,1500),
('Delhi','Kovalam',10500,4000,1200,1800),

('Pune','Kochi',6000,2500,800,1000),
('Pune','Munnar',6500,3000,900,1200),
('Pune','Alleppey',6700,2800,850,1100),
('Pune','Thekkady',7000,3500,1000,1500),
('Pune','Kovalam',7300,4000,1200,1800),

('Kolkata','Kochi',8500,2500,800,1000),
('Kolkata','Munnar',9000,3000,900,1200),
('Kolkata','Alleppey',9200,2800,850,1100),
('Kolkata','Thekkady',9500,3500,1000,1500),
('Kolkata','Kovalam',9800,4000,1200,1800),

('Ahmedabad','Kochi',7500,2500,800,1000),
('Ahmedabad','Munnar',8000,3000,900,1200),
('Ahmedabad','Alleppey',8200,2800,850,1100),
('Ahmedabad','Thekkady',8500,3500,1000,1500),
('Ahmedabad','Kovalam',8800,4000,1200,1800),

('Jaipur','Kochi',8500,2500,800,1000),
('Jaipur','Munnar',9000,3000,900,1200),
('Jaipur','Alleppey',9200,2800,850,1100),
('Jaipur','Thekkady',9500,3500,1000,1500),
('Jaipur','Kovalam',9800,4000,1200,1800),

('Lucknow','Kochi',8000,2500,800,1000),
('Lucknow','Munnar',8500,3000,900,1200),
('Lucknow','Alleppey',8700,2800,850,1100),
('Lucknow','Thekkady',9000,3500,1000,1500),
('Lucknow','Kovalam',9300,4000,1200,1800)              
""")
    con.commit()

con.commit()


llm=ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")

)
client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY", "").strip()
)
openweather_api_key=os.getenv("OPENWEATHER_API_KEY")

@tool
def weather_tool(city:str):
    """
    get weather details
    """
    
    res=requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={openweather_api_key}&units=metric")
    return res.json()

@tool
def budget_sql_tool(query:str):
    """
    Execute SQL queries on table travel_details.

    Table Name: travel_details

    Columns:
    - source_city
    - destination_city
    - flight_price
    - hotel_price
    - food_price
    - local_transport_price

    Example:
    SELECT hotel_price
    FROM travel_details
    WHERE source_city='Chennai'
    AND destination_city='Kochi';
    """

    cursor = con.cursor(dictionary=True)
    cursor.execute(query)
    data = cursor.fetchall()

    if not data:
        return "No travel data found."

    return str(data)
@tool
def famous_places_tool(query:str):
    """
    Search information about tourist places, food places, hotels, and travel destinations.
    """

    result = client.search(
        query=query,
        max_results=5
    )

    return result

agent=create_agent(
    model=llm,
    tools=[
        weather_tool,budget_sql_tool,famous_places_tool
    ]
)
@app.post("/weather_tool_call")
def weather_api(city:str=Query(...),question:str=Query(...)):
    result=agent.invoke({
       "messages":[
           {
               "role":"user",
               "content":f"""
                City:{city}
                Question:{question}
                Use weather_tool.
              """
           }
       ] 
    })
    return result

@app.post("/budget_tool_calling")
def budget_api(
    source_city:str=Query(...),
    destination_city:str=Query(...),
    question:str=Query(...)
):
    result=agent.invoke({
        "messages":[
            {
                "role":"user",
                "content":f"""
                  Source City:{source_city}
                  Destination City:{destination_city}
                  Question:{question}
                  Use budget_sql_tool.
                 """
            }
        ]
    })
    return result

@app.post("/places_tool_calling")
def places_api(city:str=Query(...),question:str=Query(...)):
    result=agent.invoke({
        "messages":[
            {
                "role":"user",
                "content":f"""
                 City:{city}
                 Question:{question}
                 Use famous_places_tool.
                """

            }
        ]
    })
    return result