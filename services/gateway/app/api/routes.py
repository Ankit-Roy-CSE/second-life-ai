from fastapi import APIRouter

router = APIRouter()

# Routes implemented in P1-A2:
#   POST /returns
#   GET  /returns/{id}
#   POST /purchase  (P2-A2)
#   GET  /passports/{id}  (P2-A2 aggregation)
#   GET  /matches/{return_id}  (P2-A2 aggregation)
#   GET  /sustainability  (P2-A2 read-model)
#   GET  /debug/events  (P0-B3 — added in coordination with B)
