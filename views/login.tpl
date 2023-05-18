% rebase('base.tpl', title="Login")

% if err:
  <div class="admonition error">
    <p class="admonition-title">Error</p>
    <p>The supplied password is not correct.</p>
  </div>
% end
% if conf_err:
  <div class="admonition error">
    <p class="admonition-title">Configuration Error</p>
    <p>You need to add <code>admin_password</code> to your <code>wmk_config.yaml</code>
      before you can use this admin page.</p>
  </div>
% end

<form action="/_/admin/login/" method="POST">
  <label>Password</label>
  <input type="password" name="password">
  <input type="submit" value="Log in">
</form>
