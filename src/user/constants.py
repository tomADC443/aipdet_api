
HTML_RESPONSE_ERROR = """
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Email Verified</title>
  <link href="https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: "Nunito Sans", Helvetica, Arial, sans-serif;
      background-color: #F2F4F6;
      color: #51545E;
      margin: 0;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
    }
    .container {
      background-color: #FFFFFF;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
      text-align: center;
      max-width: 400px;
      width: 100%;
    }
    h1 {
      color: #333333;
      font-size: 22px;
      font-weight: bold;
      margin-bottom: 20px;
    }
    p {
      font-size: 16px;
      line-height: 1.5;
      color: #51545E;
      margin-bottom: 20px;
    }
    .button {
      background-color: #22BC66;
      color: #FFFFFF;
      text-decoration: none;
      padding: 12px 20px;
      font-size: 16px;
      font-weight: bold;
      border-radius: 5px;
      display: inline-block;
      box-shadow: 0 2px 3px rgba(0, 0, 0, 0.16);
      transition: background-color 0.3s ease;
    }
    .button:hover {
      background-color: #1A944E;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Your email address could not be verified</h1>
    <p>Your email could not be verified, please contact support and include your email verification link.</p>
    <a href="mailto:tom@tpl.dev'">tom@tpl.dev</a>
  </div>
</body>
</html>
    """

HTML_RESPONSE_SUCCESS = """
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Email Verified</title>
  <link href="https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: "Nunito Sans", Helvetica, Arial, sans-serif;
      background-color: #F2F4F6;
      color: #51545E;
      margin: 0;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
    }
    .container {
      background-color: #FFFFFF;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
      text-align: center;
      max-width: 400px;
      width: 100%;
    }
    h1 {
      color: #333333;
      font-size: 22px;
      font-weight: bold;
      margin-bottom: 20px;
    }
    p {
      font-size: 16px;
      line-height: 1.5;
      color: #51545E;
      margin-bottom: 20px;
    }
    .button {
      background-color: #22BC66;
      color: #FFFFFF;
      text-decoration: none;
      padding: 12px 20px;
      font-size: 16px;
      font-weight: bold;
      border-radius: 5px;
      display: inline-block;
      box-shadow: 0 2px 3px rgba(0, 0, 0, 0.16);
      transition: background-color 0.3s ease;
    }
    .button:hover {
      background-color: #1A944E;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Email Verified!</h1>
    <p>Your email has been successfully verified. You are now ready to proceed to login.</p>
    <a href="http://aipdet.com/auth/login" class="button">Go to Login</a>
  </div>
</body>
</html>
    """
