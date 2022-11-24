#/bin/sh
rm -r build/
eleventy --formats=html,css,js,liquid,md --output=build
rm -r build/components
rm build/.eleventy.js