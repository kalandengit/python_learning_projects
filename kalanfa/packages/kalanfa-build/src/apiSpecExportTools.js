const { kalanfaName } = require('./kalanfaName');

function generateApiKeys(apiSpec, exposes) {
  // Generate a list of all the module imports that we need to expose
  // Iterate over all the exports in the kalanfa package
  return (
    Object.keys(apiSpec)
      // Filter out the export for the root package '.' as we don't need to expose that
      // nor the package.json export.
      .filter(key => key !== '.' && key !== './package.json')
      // Add the kalanfa prefix and remove the leading '.' to make a full import path
      // e.g. './urls' -> 'kalanfa/urls'
      .map(key => 'kalanfa' + key.slice(1))
      // Add the list of modules that are exposed in the kalanfa package.json
      // Unmodified, as they are already full import paths, e.g. 'vue'
      .concat(exposes)
  );
}

function getCoreExternals() {
  const kalanfaPackageJson = require('kalanfa/package.json');

  const apiSpec = kalanfaPackageJson.exports || {};

  const apiKeys = generateApiKeys(apiSpec, kalanfaPackageJson.exposes || []);

  const coreExternals = {
    // The kalanfa package itself is a special case, as it is the root of the package
    // and is not required to be imported in the core bundle, as it is the core bundle.
    kalanfa: kalanfaName,
  };

  for (const key of apiKeys) {
    coreExternals[key] = [kalanfaName, key];
  }
  return coreExternals;
}

module.exports = {
  getCoreExternals,
  generateApiKeys,
};
