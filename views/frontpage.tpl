% rebase('base.tpl', title="wmkAdmin frontpage")

<hgroup>
<h1>wmkAdmin</h1>
<h2>A simple admin system for websites built in wmk</h2>
</hgroup>

% if flash_message:
  <div class="admonition warning">
    <p class="admonition-title">Warning</p>
    <p>{{ flash_message }}</p>
  </div>
% end

  <section class="grid-sm">
    <article>
      <header>
        <h3>File management</h3>
      </header>

      <p class="larger">You can <strong>manage the files</strong> in the
        <a href="/_/admin/list/content/">content</a>,
        <a href="/_/admin/list/data/">data</a> and
        <a href="/_/admin/list/static/">static</a>
        directories. Links to these three base directories are always present in the
        navigation bar at the top.
      </p>
      <p>You can use the file manager to edit, delete, view, rename or move existing
        files, as well as to add new files, either via upload or simply by creating an
        empty file with a name of your choosing. Each change triggers a normal rebuild
        of the site.</p>
    </article>

    <article>
      <header>
        <h3>Rebuild site</h3>
      </header>

      <p class="ta-c">
        <a href="/_/admin/build/" role="button" class="larger">Normal build</a>
        <a href="/_/admin/build/?hard=1" role="button" class="larger">Hard rebuild</a>
      </p>

      <p><strong>Note:</strong> A hard rebuild means that before building the site,
        both the rendering cache and all files in <code>htdocs/</code> are deleted. On
        a large or complex site, this may take several minutes! Nevertheless, a
        hard rebuild may sometimes be necessary if you have deleted or moved
        files or directories.</p>
    </article>
  </section>

<h2>Configuration file</h2>

<p>The contents of the <code>wmk_config.yaml</code> configuration file for
  this site can be seen below. Note that this is purely for your reference; you
  cannot change the configuration via this admin page.</p>

<pre><code>{{ wmk_config_contents }}</code></pre>

<h2>TODO</h2>

<p>Perhaps to be added later:</p>

<ul>
  <li>Committing changes (automatically) to git, if the site is under
version control. Pushing, pulling as manual actions?</li>
  <li>Editing <code>wmk_config.yaml</code>.</li>
  <li>Add <code>assets</code>?</li>
  <li>Report on build errors.</li>
  <li>Validate yaml files before saving?</li>
  <li>Better editor for text-based formats.</li>
  <li>Change behaviour based on some wmk config settings.</li>
</ul>
