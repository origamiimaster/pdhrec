module.exports = function(eleventyConfig) {
    eleventyConfig.addPassthroughCopy("commandernames.json");
    eleventyConfig.addPassthroughCopy("favicon-16x16.png");
    eleventyConfig.addPassthroughCopy("favicon-32x32.png");
    eleventyConfig.addPassthroughCopy("favicon.ico");
    eleventyConfig.addPassthroughCopy("android-chrome-192x192.png");
    eleventyConfig.addPassthroughCopy("android-chrome-512x512.png");
    eleventyConfig.addPassthroughCopy("apple-touch-icon.png");
    eleventyConfig.addPassthroughCopy("browserconfig.xml");
    eleventyConfig.addPassthroughCopy("mstile-150x150.png");
    eleventyConfig.addPassthroughCopy("safari-pinned-tab.svg");
    eleventyConfig.addPassthroughCopy("site.webmanifest");

    eleventyConfig.addFilter("commandernamefix", function(value) {
        console.log(value)
        return value;
    });

};
