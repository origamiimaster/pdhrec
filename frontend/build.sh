#/bin/sh
eleventy --formats=html,css,js,liquid --output=build
rm -r build/components
rm build/.eleventy.js