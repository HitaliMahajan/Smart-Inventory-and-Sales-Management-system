from flask import Blueprint
seller = Blueprint('seller', __name__)
from app.seller import routes