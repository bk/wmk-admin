% rebase('base.tpl', title="Login")

% if err:
  <div class="admonition error">
    <p class="admonition-title">Error</p>
    <p>The supplied password is not correct.</p>
  </div>
% end

<form action="/_/admin/login/" method="POST">
  <label>Password</label>
  <input type="password" name="password">
  <input type="submit" value="Log in">
</form>
