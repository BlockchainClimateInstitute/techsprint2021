from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from sqlalchemy import create_engine
from sqlalchemy import MetaData, Table
from sqlalchemy.orm import sessionmaker
from flask import Blueprint, render_template, abort

from admin.views import admin


api_v1 = Blueprint("api", __name__, url_prefix="/swagger_docs")


api = Api(api_v1, version='0.0.1', title='TCFD Risks API', #url_scheme='https',
          licence= "MIT", description='MicroService for location mapping')

# User for only read access to DB (only these tables)
# CREATE USER techsprint WITH PASSWORD 'techsprintPa55w0rd';
# GRANT CONNECT ON DATABASE postgres TO techsprint;
# GRANT USAGE ON SCHEMA public TO techsprint;
# GRANT SELECT ON epcaddresses TO techsprint;
# GRANT SELECT ON epcvar TO techsprint;
engine = create_engine(
    'postgresql+psycopg2://techsprint:techsprintPa55w0rd@golden-source-2020.cyozpdhauzu4.us-east-2.rds.amazonaws.com:5432/postgres')
connection = engine.connect()
metadata = MetaData()
address_df = Table('epcaddresses', metadata, autoload=True, autoload_with=engine)
risk_df = Table('epcvar', metadata, autoload=True, autoload_with=engine)


Session = sessionmaker(bind=engine)
s1 = Session()


# Adress List  Models
unit_request = api.model(
    "unit_request", {
        "version": fields.String(required=True, description="The version of the schema."),
        "unitList": fields.List(fields.String, required=True, description="The list of unit postcodes."),
        "user": fields.String(required=False, description="The user of the call.")
    }
)
# Example Json to send in Swagger Request
# {"unit_request": { "version": "0.0.1", "unitList": ["SW128PW", "E105QD"]}}
addressList = api.model(
    "addressList", {
        "buildingId": fields.String(required=True, description="Buildingid."),
        "address1": fields.String(required=True, description="Addressline1."),
        "address2": fields.String(required=True, description="Addressline2."),
        "address3": fields.String(required=True, description="Addressline3.")
    }
)
unitLocation = api.model(
    "location", {
        "latitude": fields.Float(required=True, description="GPS coordinate (latitude) for unit location (postcode)."),
        "longitude": fields.Float(required=True,
                                  description="GPS coordinate (longitude) for unit location (postcode).")
    }
)
unitList = api.model(
    "unitList", {
        "unit": fields.String(required=True, description="Unit/Postcode."),
        "location": fields.Nested(unitLocation, required=True,
                                  description="Geo Location of the Unit (not the addresses)."),
        "addressList": fields.List(fields.Nested(addressList, required=True, description="Address detail")
                                   , required=True, description="The list of Address for the Unit"),
        "comment": fields.String(required=True, description="Contains information if PostCode not valid.")
    }
)
unit_response = api.model(
    "unit_response", {
        "success": fields.Boolean(required=True, description="The status of work"),
        "version": fields.String(required=False, description="The version of the schema used"),
        "unitList": fields.List(fields.Nested(unitList, required=True,
                                              description="Unit object having all addresss and location detail.")
                                , required=True, description="The list of Units."),
        "user": fields.String(required=False, description="The user of the call.")
    }
)

# Risk Models
risk_request = api.model(
    "risk_request", {
        "version": fields.String(required=True, description="The version of the schema."),
        "buildingList": fields.List(fields.String, required=True, description="Array containing buildings information"),
        "user": fields.String(required=False, description="The user of the call.")
    }
)

# Example Json to send in Swagger Request
# {"risk_request": { "version": "0.0.1", "buildingList": ["1900962178"]}}
riskColumn = api.model(
    "riskColumn", {
        "name": fields.String(required=True, description="Risk Column Name for the Real Estate Asset"),
        "value": fields.Float(required=True, description="Physical Value at Risk for the Real Estate Asset"),
    }
)
riskColumnText = api.model(
    "riskColumn", {
        "name": fields.String(required=True, description="Risk Column Name for the Real Estate Asset"),
        "value": fields.String(required=True, description="Physical Value at Risk for the Real Estate Asset"),
    }
)
buildingList = api.model(
    "buildingList", {
        "buildingId": fields.String(required=True, description="EPC ID of the Real Estate Asset."),
        "address1": fields.String(required=True,
                                  description="Exact address of the Real Estate Asset (as defined by Address1 in EPC)."),
        "address2": fields.String(required=True,
                                  description="Exact address of the Real Estate Asset (as defined by Address2 in EPC)."),
        "address3": fields.String(required=True,
                                  description="Exact address of the Real Estate Asset (as defined by Address3 in EPC)."),
        "unit": fields.String(required=True, description="Postcode of the property."),
        "unitElevation": fields.String(required=True, description="Elevation of the unit lat/lon."),
        "unitLocation": fields.Nested(unitLocation, required=True, description=" Geo Location of the Unit"),
        "price": fields.String(required=True, description="Estimated price for the Property (Real Estate Asset)."),
        "climateRisk": fields.List(
            fields.Nested(riskColumn, required=True, description="Risk of the specific Real Estate Asset.")),
        "climateRiskText": fields.List(
            fields.Nested(riskColumnText, required=True, description="Risk of the specific Real Estate Asset.")),
        "comment": fields.String(required=True, description="Contains information if BuildingID not valid.")
    }
)
risk_response = api.model(
    "risk_response", {
        "success": fields.Boolean(required=True, description="The status of work"),
        "version": fields.String(required=True,
                                 description="Describes the current version of the payload, follows the format X.X.X"),
        "buildingList": fields.Nested(buildingList, required=True,
                                      description="Array containing buildings information"),
        "user": fields.String(required=False,
                              description="Section of the payload that describes User Context Information")
    })

# See more about this example here:
# https://github.com/python-restx/flask-restx/blob/41b3b591b4be89d5d27e571dd3a75f849d4455ca/examples/todo_blueprint.py
# https://github.com/python-restx/flask-restx/blob/0dc1c3c966d0394da4b807e491225e90f46b27b8/doc/swagger.rst

# Parsers
parser_unit_request = api.parser()
parser_unit_request.add_argument("unit_request", type=unit_request, required=True, help="Unit Request Schema")

parser_risk_request = api.parser()
parser_risk_request.add_argument("risk_request", type=risk_request, required=True, help="Risk Request Schema")


# Namespaces
ns1 = api.namespace('address_service', description='Address Listing operations')
ns2 = api.namespace('risk_service', description='Risk Listing operations')


@ns1.route('/')
class unit(Resource):
    '''TODO'''

    @api.doc(parser=parser_unit_request)
    @api.expect(unit_request, validate=True)
    @api.marshal_with(unit_response, code=201)
    def post(self):
        '''Get full location information'''
        args = parser_unit_request.parse_args()
        units = args["unit_request"]["unitList"]

        # Loop over the postcodes/units
        units_reponse = []
        for unit in units:
            # Remove whitespaces
            unit_no_space = unit.replace(' ', '').upper()

            # Get results from query
            unit_query = s1.query(address_df).filter_by(Postcode=unit_no_space).all()

            if len(unit_query) == 0:
                units_reponse.append({"unit": unit_no_space,
                                      "location": {
                                          'latitude': None,
                                          'longitude': None,
                                      },
                                      "addressList": [],
                                      "comment": "Error. PostCode not found in EPC list"
                                      })
            else:
                # Get all addresses and lat/lon
                address_data = []
                long = None
                lat = None
                for index, epcaddress in enumerate(unit_query):
                    address_data.append({
                        'buildingId': epcaddress.BUILDING_REFERENCE_NUMBER,
                        'address1': epcaddress.Address,
                        'address2': 'Constant Add 2',
                        'address3': 'Constant Add 3',
                    })
                    if index == 0:
                        long = float(epcaddress.PostcodeLongitude)
                        lat = float(epcaddress.PostcodeLatitude)

                # Store results for this specific postcode/unit before processing next one
                units_reponse.append({"unit": unit_no_space,
                                      "location": {
                                          'latitude': long,
                                          'longitude': lat,
                                      },
                                      "addressList": address_data,
                                      "comment": "Success. PostCode found in EPC list"
                                      })

        return {"success": True,
                "version": args["unit_request"]["version"],
                "unitList": units_reponse,
                "user": 'BCI'
                }, 201


@ns2.route('/')
class risk(Resource):
    '''TODO'''

    @api.doc(parser=parser_risk_request)
    @api.expect(risk_response, validate=True)
    @api.marshal_with(risk_response, code=201)
    def post(self):
        '''Get full location information'''
        args = parser_risk_request.parse_args()
        buildingList = args["risk_request"]["buildingList"]

        buildings_reponse = []
        for building in buildingList:

            # Get results from query
            address_query = s1.query(address_df).filter_by(BUILDING_REFERENCE_NUMBER=building).first()
            risk_query = s1.query(risk_df).filter_by(BUILDING_REFERENCE_NUMBER=building).first()

            # Need to try to identify the way to loop over the columns (this does not work yet)
            # all_results = {}
            # for col in add_query_risk.columns.keys():
            #    all_results[col] = getattr(add_query_risk, col)

            if len(address_query) == 0:
                # Store results for this specific postcode/unit before processing next one
                buildings_reponse.append({"unit": None,
                                          "unitLocation": {
                                              'latitude': None,
                                              'longitude': None,
                                          },
                                          "buildingId": building,
                                          "address1": None,
                                          "address2": 'Constant Add 2',
                                          "address3": 'Constant Add 3',
                                          "unitElevation": 'TODO',
                                          "price": None,
                                          "climateRisk": [],
                                          "comment": "Error. BuildingID not found in EPC list"
                                          })
            else:
                # Store results for this specific postcode/unit before processing next one
                buildings_reponse.append({"unit": address_query.Postcode,
                                          "unitLocation": {
                                              'latitude': address_query.PostcodeLongitude,
                                              'longitude': address_query.PostcodeLatitude,
                                          },
                                          "buildingId": building,
                                          "address1": address_query.Address,
                                          "address2": 'Constant Add 2',
                                          "address3": 'Constant Add 3',
                                          "unitElevation": 'TODO',
                                          "price": risk_query.Price,
                                          "climateRisk": [
                                              {
                                                  "name": "CRREM_2020_15",
                                                  "value": risk_query.CRREM_2020_15
                                              },
                                              {
                                                  "name": "CRREM_2025_15",
                                                  "value": risk_query.CRREM_2025_15
                                              },
                                              {
                                                  "name": "CRREM_2030_15",
                                                  "value": risk_query.CRREM_2030_15
                                              },
                                              {
                                                  "name": "CRREM_2035_15",
                                                  "value": risk_query.CRREM_2035_15
                                              },
                                              {
                                                  "name": "CRREM_2040_15",
                                                  "value": risk_query.CRREM_2040_15
                                              },
                                              {
                                                  "name": "CRREM_2045_15",
                                                  "value": risk_query.CRREM_2045_15
                                              },
                                              {
                                                  "name": "CRREM_2050_15",
                                                  "value": risk_query.CRREM_2050_15
                                              },
                                              {
                                                  "name": "CRREM_2020_20",
                                                  "value": risk_query.CRREM_2020_20
                                              },
                                              {
                                                  "name": "CRREM_2025_20",
                                                  "value": risk_query.CRREM_2025_20
                                              },
                                              {
                                                  "name": "CRREM_2030_20",
                                                  "value": risk_query.CRREM_2030_20
                                              },
                                              {
                                                  "name": "CRREM_2035_20",
                                                  "value": risk_query.CRREM_2035_20
                                              },
                                              {
                                                  "name": "CRREM_2040_20",
                                                  "value": risk_query.CRREM_2040_20
                                              },
                                              {
                                                  "name": "CRREM_2045_20",
                                                  "value": risk_query.CRREM_2045_20
                                              },
                                              {
                                                  "name": "CRREM_2050_20",
                                                  "value": risk_query.CRREM_2050_20
                                              },
                                              {
                                                  "name": "PHYSICAL_2020_15",
                                                  "value": risk_query.PHYSICAL_2020_15
                                              },
                                              {
                                                  "name": "PHYSICAL_2025_15",
                                                  "value": risk_query.PHYSICAL_2025_15
                                              },
                                              {
                                                  "name": "PHYSICAL_2030_15",
                                                  "value": risk_query.PHYSICAL_2030_15
                                              },
                                              {
                                                  "name": "PHYSICAL_2035_15",
                                                  "value": risk_query.PHYSICAL_2035_15
                                              },
                                              {
                                                  "name": "PHYSICAL_2040_15",
                                                  "value": risk_query.PHYSICAL_2040_15
                                              },
                                              {
                                                  "name": "PHYSICAL_2045_15",
                                                  "value": risk_query.PHYSICAL_2045_15
                                              },
                                              {
                                                  "name": "PHYSICAL_2050_15",
                                                  "value": risk_query.PHYSICAL_2050_15
                                              },
                                              {
                                                  "name": "PHYSICAL_2020_20",
                                                  "value": risk_query.PHYSICAL_2020_20
                                              },
                                              {
                                                  "name": "PHYSICAL_2025_20",
                                                  "value": risk_query.PHYSICAL_2025_20
                                              },
                                              {
                                                  "name": "PHYSICAL_2030_20",
                                                  "value": risk_query.PHYSICAL_2030_20
                                              },
                                              {
                                                  "name": "PHYSICAL_2035_20",
                                                  "value": risk_query.PHYSICAL_2035_20
                                              },
                                              {
                                                  "name": "PHYSICAL_2040_20",
                                                  "value": risk_query.PHYSICAL_2040_20
                                              },
                                              {
                                                  "name": "PHYSICAL_2045_20",
                                                  "value": risk_query.PHYSICAL_2045_20
                                              },
                                              {
                                                  "name": "PHYSICAL_2050_20",
                                                  "value": risk_query.PHYSICAL_2050_20
                                              },
                                              {
                                                  "name": "GLOBAL_RANK_CRREM_2050_15",
                                                  "value": risk_query.GLOBAL_RANK_CRREM_2050_15
                                              },
                                              {
                                                  "name": "LOCAL_RANK_CRREM_2050_15",
                                                  "value": risk_query.LOCAL_RANK_CRREM_2050_15
                                              }
                                          ],
                                          "climateRiskText": [
                                              {
                                                  "name": "CURRENT_ENERGY_RATING",
                                                  "value": risk_query.CURRENT_ENERGY_RATING
                                              },
                                              {
                                                  "name": "POTENTIAL_ENERGY_RATING",
                                                  "value": risk_query.POTENTIAL_ENERGY_RATING
                                              },
                                              {
                                                  "name": "PROPERTY_TYPE",
                                                  "value": risk_query.PROPERTY_TYPE
                                              },
                                              {
                                                  "name": "TOTAL_FLOOR_AREA",
                                                  "value": risk_query.TOTAL_FLOOR_AREA
                                              },
                                              {
                                                  "name": "Outcode",
                                                  "value": risk_query.Outcode
                                              },
                                          ],
                                          "comment": "Success. BuildingID found in EPC list"
                                          })

        return {"success": True,
                "version": args["risk_request"]["version"],
                "buildingList": buildings_reponse,
                "user": 'BCI'
                }, 201

    s1.close()


if __name__ == '__main__':
    app = Flask(__name__)
    CORS(app)
    app.config['JSON_SORT_KEYS'] = False
    app.register_blueprint(api_v1)
    app.register_blueprint(admin, url_prefix='/')
    app.run(
        host='0.0.0.0',
        debug=True,
        port='5000'
    )
