const express = require("express");

const app = express();

const port = process.env.PORT || 3000;

app.get("/", (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>DevOps Portfolio App</title>
      </head>
      <body>
        <h1>DevOps Portfolio App</h1>
        <p>Application is running successfully.</p>
      </body>
    </html>
  `);
});

app.listen(port, () => {
  console.log(`Application listening on port ${port}`);
});
