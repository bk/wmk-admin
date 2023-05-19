% rebase('base.tpl', title="wmkAdmin frontpage")

<hgroup>
<h1>wmkAdmin</h1>
% if site_title:
  <h2>for the website <strong class="text-accent">{{ site_title }}</strong></h2>
% else:
  <h2>A simple admin system for websites built in wmk</h2>
% end
</hgroup>

% if flash_message:
  <div class="admonition {{ msg_status }}">
    <p class="admonition-title">{{ msg_status.title() }}</p>
    <p>{{ flash_message }}</p>
  </div>
% end

  <section class="grid-sm c2">
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

    <article>
      <header>
        <h3>Edit configuration</h3>
      </header>
      <p class="ta-c">
        <a href="/_/admin/edit-config/" role="button" class="larger">Edit wmk_config.yaml</a>
      </p>
      <p><code>wmk_config.yaml</code> is the main configuration file for each site built with wmk. Take care when you edit it, since an invalid file will prevent your site from being built and thus updated.</p>
    </article>

    <article>
      <header>
        <h3>View site</h3>
      </header>
      <p class="ta-c">
        <a href="/" role="button" class="larger">View the site</a>
      </p>
      <p>In addition to the admin pages, wmkAdmin runs a webserver for previewing the development version of the website. (You can see that it is the development version from the prominent link to Admin in the lower right corner of each page.)</p>
    </article>
  </section>

% if False:

<h2>TODO</h2>

<p>Perhaps to be added later:</p>

<ul>
  <li>Committing changes (automatically) to git, if the site is under
version control. Pushing, pulling as manual actions?</li>
  <li>Add <code>assets</code> to directories that can be managed?</li>
  <li>Report on build errors.</li>
  <li>View logs.</li>
  <li>Validate yaml files before saving?</li>
  <li>Better editor for text-based formats.</li>
</ul>

% end
