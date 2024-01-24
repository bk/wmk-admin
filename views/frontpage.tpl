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
        <a href="/_/admin/list/data/">data</a>,
        <a href="/_/admin/list/static/">static</a> and
        <a href="/_/admin/list/templates/">templates</a>
        folders. Links to these four base directories are always present in the
        navigation bar at the top.
      </p>
      <p>You can use the file manager to <em>edit</em>, <em>delete</em>,
        <em>view</em> or <em>rename/move</em> existing files, as well as to <em>add</em>
        new content, either via <em>upload</em> or simply by creating an
        <em>empty</em> page or file.</p>
    </article>

    <article>
      <header>
        <h3>Rebuild {{ 'or publish' if deploy else 'site' }}</h3>
      </header>

      <p class="ta-c">
        <a href="/_/admin/build/" role="button" class="larger">
          % include('svg/command.svg')
          Normal build</a>
        <a href="/_/admin/build/?hard=1" role="button" class="larger bg-error">
          % include('svg/coffee.svg')
          Hard rebuild</a>
      </p>

      <p{{! ' class="m-0"' if deploy else '' }}><strong>Note:</strong>
        A hard rebuild means that before building the site,
        both the rendering cache and all files in <code>htdocs/</code> are deleted. On
        a large or complex site, this may take several minutes and should only
        be done for a good reason.</p>
      % if deploy:
        <p class="ta-c">
          <a href="/_/admin/deploy/" role="button" class="larger bg-success">
          % include('svg/upload-cloud.svg')
          Publish site</a>
        </p>
      % end
    </article>

    <article>
      <header>
        <h3>Edit configuration</h3>
      </header>
      <p class="ta-c">
        <a href="/_/admin/edit-config/" role="button" class="larger">
          % include('svg/edit.svg')
          Edit wmk_config.yaml</a>
      </p>
      <p><code>wmk_config.yaml</code> is the main configuration file for each site built with wmk. Take care when you edit it, since an invalid file will prevent your site from being built and thus updated.</p>
    </article>

    <article>
      <header>
        <h3>View site</h3>
      </header>
      <p class="ta-c">
        <a href="/" role="button" class="larger">
          % include('svg/eye.svg')
          View the site</a>
      </p>
      <p>In addition to the admin pages, wmkAdmin runs a webserver for previewing the <strong>development version</strong> of the website. (You can see that it is the development version from the prominent link to Admin in the lower right corner of each page.)</p>
    </article>
  </section>

% if status_info and (status_info['deployed_date'] or status_info['git_status']):
  <div class="mt-5">
    <div class="admonition info">
      <p class="admonition-title">Status information</p>
      <p><strong>Last deployment:</strong> {{ str(status_info['deployed_date'])[:19] if status_info['deployed_date'] else 'UNKNOWN' }}</p>
      % if status_info['git_last_commit']:
        <p><strong>Last commit:</strong> {{ status_info['git_last_commit'] }}</p>
      % end
      % if status_info['git_status']:
        <p><strong>Modified (<em>M</em>), deleted (<em>D</em>) or new/unknown (<em>??</em>) files:</strong></p>
        <pre class="smaller"><code>{{ status_info['git_status'] }}</code></pre>
      % elif status_info['git_last_commit']:
        <p><strong>Up to date:</strong> No pending changes waiting to be published.</p>
      % end
    </div>
  </div>
% end
