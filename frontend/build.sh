#!/bin/sh
rm -r build/
npx @11ty/eleventy --formats=html,css,js,liquid,md --output=build
rm -r build/components
rm build/.eleventy.js