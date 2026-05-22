from flask import Blueprint, g, jsonify

from extensions import get_db
from services.revision_service import get_revision_pack
from utils.jwt_utils import token_required

revisions_bp = Blueprint("revisions", __name__, url_prefix="/api/revisions")


@revisions_bp.route("", methods=["GET"])
@token_required()
def revision_pack():
    return jsonify(get_revision_pack(get_db(), g.current_user["sub"]))
