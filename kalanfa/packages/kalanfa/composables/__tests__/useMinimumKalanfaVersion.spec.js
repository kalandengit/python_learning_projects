import useMinimumKalanfaVersion from '../useMinimumKalanfaVersion';

describe(`useMinimumKalanfaVersion`, () => {
  describe(`returns isMinimumKalanfaVersion function defaulting to 0.15+`, () => {
    const { isMinimumKalanfaVersion } = useMinimumKalanfaVersion();

    it(`lower version is detected, with 0.15.0 as default`, () => {
      expect(isMinimumKalanfaVersion('0.14.99')).toBe(false);
    });

    it(`same version is detected, with 0.15.0 as default`, () => {
      expect(isMinimumKalanfaVersion('0.15.0')).toBe(true);
    });
  });

  describe(`returns isMinimumKalanfaVersion function for custom version`, () => {
    const { isMinimumKalanfaVersion } = useMinimumKalanfaVersion(0, 16, 0);

    it(`lower version is detected, without default`, () => {
      expect(isMinimumKalanfaVersion('0.15.4')).toBe(false);
    });

    it(`same version is detected, without default`, () => {
      expect(isMinimumKalanfaVersion('0.16.0')).toBe(true);
    });

    it(`higher version is detected, without default`, () => {
      expect(isMinimumKalanfaVersion('0.16.1')).toBe(true);
    });

    it(`check beta versions work when betas are included`, () => {
      expect(isMinimumKalanfaVersion('0.16.0-b4')).toBe(false);
    });

    it(`check beta versions work fine with upper values`, () => {
      expect(isMinimumKalanfaVersion('0.16.1-b4')).toBe(true);
    });
  });

  it(`check beta versions work when betas are included`, () => {
    const { isMinimumKalanfaVersion } = useMinimumKalanfaVersion(0, 16);
    expect(isMinimumKalanfaVersion('0.16.0-b4')).toBe(true);
  });

  it(`check beta versions work fine with equal values`, () => {
    const { isMinimumKalanfaVersion } = useMinimumKalanfaVersion(0, 16, 1);
    expect(isMinimumKalanfaVersion('0.16.1-b4')).toBe(false);
  });
});
