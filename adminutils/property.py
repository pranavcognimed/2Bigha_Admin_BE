from schemas.properties import GeoJSONFeature, PolygonGeometry, PointGeometry, Properties, GeoJSONResponse, PropertyImage
from geoalchemy2.shape import to_shape
from models.properties import Property
from typing import List
import logging
import json

def convert_properties_to_geojson(properties: List[Property]) -> GeoJSONResponse:
    features = []
    for prop in properties:
        try:
            polygon_geojson = json.loads(prop.geom) if isinstance(prop.geom, str) else prop.geom
            polygon_coordinates = polygon_geojson.get("coordinates", [])
            
            if not isinstance(polygon_coordinates, list):
                logging.error(f"Coordinates not a list for property {prop.id}")
                polygon_coordinates = [[[]]]
            elif len(polygon_coordinates) == 0:
                polygon_coordinates = [[[]]]
            elif any(not isinstance(x, list) for x in polygon_coordinates):
                logging.error(f"Coordinates have improper nesting for property {prop.id}")
                polygon_coordinates = [[[]]]
            elif polygon_coordinates and isinstance(polygon_coordinates[0], list):
                if polygon_coordinates[0] and not isinstance(polygon_coordinates[0][0], list):
                    polygon_coordinates = [polygon_coordinates]
                elif polygon_coordinates[0] and isinstance(polygon_coordinates[0][0], list) and isinstance(polygon_coordinates[0][0][0], list):
                    polygon_coordinates = polygon_coordinates[0]
        except (json.JSONDecodeError, AttributeError, ValueError, IndexError, TypeError) as e:
            logging.error(f"Error processing property {prop.id} geometry: {str(e)}")
            polygon_coordinates = [[[]]]

        flattened_coordinates = []
        try:
            if polygon_coordinates and isinstance(polygon_coordinates[0], list):
                if polygon_coordinates[0] and isinstance(polygon_coordinates[0][0], list):
                    flattened_coordinates = polygon_coordinates
                else:
                    flattened_coordinates = [polygon_coordinates]
            else:
                flattened_coordinates = [[[]]]
        except (IndexError, TypeError) as e:
            logging.error(f"Error flattening coordinates for property {prop.id}: {str(e)}")
            flattened_coordinates = [[[]]]

        centroid_geom = to_shape(prop.centroid) if prop.centroid else None
        centroid_coordinates = list(centroid_geom.coords)[0] if centroid_geom else None

        # Convert PropertyImage objects to PropertyImage schema
        image_list = [
            PropertyImage(
                id=image.id,
                image_url=image.image_url,
                uploaded_at=image.uploaded_at
            ) for image in prop.images
        ]

        feature = GeoJSONFeature(
            type="Feature",
            geometry=PolygonGeometry(
                type="Polygon",
                coordinates=flattened_coordinates
            ),
            properties=Properties(
                id=prop.id,
                property_name=prop.property_name,
                owner_name=prop.owner_name,
                property_type=prop.type,
                price=float(prop.price) if prop.price else None,
                area_sq_m=float(prop.area_sq_m) if prop.area_sq_m else None,
                unit=prop.unit,
                murabba=prop.murabba,
                khasra=prop.khasra,
                khewat=prop.khewat,
                khata=prop.khata,
                state=prop.state,
                district=prop.district,
                tehsil=prop.tehsil,
                village=prop.village,
                verified=prop.verified,
                available=prop.available,
                visits=prop.visits,
                created_at=prop.created_at,
                updated_at=prop.updated_at,
                status=prop.status,
                user_uploaded=prop.user_uploaded,
                phone=prop.phone,
                email=prop.email,
                flag_reason=prop.flag_reason,
                centroid=PointGeometry(
                    type="Point",
                    coordinates=[centroid_coordinates[0], centroid_coordinates[1]]
                ) if centroid_coordinates else None,
                images=image_list
            ),
            images=image_list
        )
        features.append(feature)
    
    return GeoJSONResponse(type="FeatureCollection", features=features)