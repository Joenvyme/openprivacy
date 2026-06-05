const { publicSiteBase, supabaseFetch } = require("./_lib.js");

module.exports = async (req, res) => {
  if (req.method !== "GET") {
    res.statusCode = 405;
    res.setHeader("Content-Type", "text/plain; charset=utf-8");
    res.end("Method not allowed");
    return;
  }

  const token = String(req.query?.token || "").trim();
  const site = publicSiteBase();

  if (!token || !/^[a-f0-9]{64}$/i.test(token)) {
    res.statusCode = 302;
    res.setHeader("Location", `${site}/#acces?verify=invalid`);
    res.end();
    return;
  }

  try {
    const lookup = await supabaseFetch(
      `openprivacy_licenses?verify_token=eq.${encodeURIComponent(token)}&select=id,license_key,verify_token_expires_at,status&limit=1`
    );
    if (!lookup.ok) {
      res.statusCode = 302;
      res.setHeader("Location", `${site}/#acces?verify=error`);
      res.end();
      return;
    }

    const rows = await lookup.json();
    if (rows.length === 0) {
      res.statusCode = 302;
      res.setHeader("Location", `${site}/#acces?verify=invalid`);
      res.end();
      return;
    }

    const row = rows[0];
    const expires = row.verify_token_expires_at
      ? new Date(row.verify_token_expires_at).getTime()
      : 0;
    if (!expires || Date.now() > expires) {
      res.statusCode = 302;
      res.setHeader("Location", `${site}/#acces?verify=expired`);
      res.end();
      return;
    }

    const patch = await supabaseFetch(
      `openprivacy_licenses?id=eq.${encodeURIComponent(row.id)}`,
      {
        method: "PATCH",
        prefer: "return=minimal",
        body: {
          status: "active",
          email_verified_at: new Date().toISOString(),
          verify_token: null,
          verify_token_expires_at: null,
        },
      }
    );

    if (!patch.ok) {
      res.statusCode = 302;
      res.setHeader("Location", `${site}/#acces?verify=error`);
      res.end();
      return;
    }

    const keyParam = encodeURIComponent(row.license_key);
    res.statusCode = 302;
    res.setHeader("Location", `${site}/#acces?verify=ok&key=${keyParam}`);
    res.end();
  } catch (err) {
    console.error(err);
    res.statusCode = 302;
    res.setHeader("Location", `${site}/#acces?verify=error`);
    res.end();
  }
};
