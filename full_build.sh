python generate_frontend_doc.py
cd frontend
rm -rf build/
eleventy --formats=html,css,js,liquid,md --output=build
