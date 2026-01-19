/**
 * Test file for CommonJS pattern support.
 */

// Named function expression assignment
app.handle = function handle(req, res) {
  console.log('test');
};

// Another named function
res.json = function json(obj) {
  return obj;
};

// Arrow function assignment
app.middleware = (req, res, next) => {
  next();
};

// Async function expression
app.fetch = async function fetch(url) {
  return await fetch(url);
};

// Module exports pattern
module.exports.helper = function helper(data) {
  return data;
};

// Prototype assignment
Response.prototype.send = function send(body) {
  return body;
};

// Anonymous function (uses property name "anon" for indexing)
app.anon = function() {
  return null;
};
