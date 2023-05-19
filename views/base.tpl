<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="/_/css/avec.min.css" type="text/css">
    <link rel="stylesheet" href="/_/css/wmk-admin.css" type="text/css">
  </head>
  <body>
    <header class="reverse-theme">
      <div class="container items-fixed items-max-md">
        <nav>
          <ul>
            <li><a href="/_/admin/" class="text brand larger"><strong>wmkAdmin</strong></a></li>
          </ul>
          <ul class="mr-a">
            <li><a href="/_/admin/list/content/" class="text">Content</a></li>
            <li><a href="/_/admin/list/data/" class="text">Data</a></li>
            <li><a href="/_/admin/list/static/" class="text">Static</a></li>
          </ul>
          % if not title == 'Login':
          <ul>
            <li><a href="/_/admin/logout/" role="button" style="margin:0; padding:0 var(--spacing)">Log out</a></li>
          </ul>
          % end
        </nav>
      </div>
    </header>
    <main class="items-fixed items-max-md">
      {{! base }}
    </main>
    <footer class="reverse-theme">
      <p class="ta-c">
        <a href="https://github.com/bk/wmk-admin/" class="plain" target="_blank">wmkAdmin on GitHub</a>
      </p>
    </footer>
  </body>
</html>
