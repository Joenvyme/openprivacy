const { sendJson } = require("./_lib.js");

module.exports = (req, res) => {
  const origin = req.headers.origin || req.headers.Origin;
  sendJson(
    res,
    200,
    {
      ok: true,
      supabase_configured: Boolean(
        process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY
      ),
    },
    origin
  );
};
