python generate_frontend_doc.py
cd frontend
rm -rf build/
npx @11ty/eleventy --formats=html,css,js,liquid,md --output=build
