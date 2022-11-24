module.exports = function(eleventyConfig) {
    eleventyConfig.addPassthroughCopy("commandernames.json");

    eleventyConfig.addFilter("commandernamefix", function(value) {
        console.log(value)
        return value;
    });

};
  