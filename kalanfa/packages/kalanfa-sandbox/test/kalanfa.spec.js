import Mediator from '../src/mediator';
import Kalanfa from '../src/kalanfa';
import { nameSpace } from '../src/base';

describe('the kalanfa shim', () => {
  let kalanfa, mediator;
  beforeEach(() => {
    mediator = new Mediator(window);
    kalanfa = new Kalanfa(mediator);
    kalanfa.__setShimInterface();
  });
  describe('__setShimInterface method', () => {
    it('should set kalanfa shim property', () => {
      expect(kalanfa.shim).not.toBeUndefined();
    });
  });
  describe('iframeInitialize method', () => {
    it('should set a "kalanfa" property on object', () => {
      const obj = {};
      kalanfa.iframeInitialize(obj);
      expect(obj.kalanfa).toEqual(kalanfa.shim);
    });
  });

  // methods
  let response, id, mockMessage, mockMediatorPromise;

  describe('getContentById method', () => {
    id = 'abc123';
    mockMessage = {
      data: { dataType: 'Model', id: 'abc123' },
      event: 'datarequested',
      nameSpace,
    };
    response = { node: { id: 'abc123' } };
    beforeEach(function () {
      mockMediatorPromise = jest
        .spyOn(kalanfa.mediator, 'sendMessageAwaitReply')
        .mockResolvedValue(response);
    });
    it('should be called once', () => {
      kalanfa.shim.getContentById(id);
      expect(mockMediatorPromise).toHaveBeenCalled();
    });
    it('should be called with the correct event, data, and namespace', () => {
      kalanfa.shim.getContentById(id);
      expect(mockMediatorPromise).toHaveBeenCalledWith(mockMessage);
    });
    it('should return a promise that resolves to a ContentNode object', () => {
      return kalanfa.shim.getContentById(id).then(data => {
        expect(data).toEqual(response);
      });
    });
  });

  describe('getContentByFilter method', () => {
    const options = { page: 1, pageSize: 50, parent: 'self' };
    response = { page: 1, pageSize: 50, results: [{ id: 'abc123' }, { id: 'def456' }] };
    beforeEach(function () {
      mockMessage = {
        data: { dataType: 'Collection', options: options },
        event: 'datarequested',
        nameSpace,
      };
      mockMediatorPromise = jest
        .spyOn(kalanfa.mediator, 'sendMessageAwaitReply')
        .mockResolvedValue(response);
    });
    it('should be called once', () => {
      kalanfa.shim.getContentByFilter(options);
      expect(mockMediatorPromise).toHaveBeenCalled();
    });
    it('should be called with the correct event, data, and namespace', () => {
      kalanfa.shim.getContentByFilter(options);
      expect(mockMediatorPromise).toHaveBeenCalledWith(mockMessage);
    });
    it('should return a promise that resolves to pagination object that contains an array of metadata objects', () => {
      return kalanfa.shim.getContentByFilter().then(data => {
        expect(data).toEqual(response);
      });
    });
  });

  describe('navigateTo method', () => {
    it('should return a promise', () => {
      expect(kalanfa.shim.navigateTo()).toBeInstanceOf(Promise);
    });
  });

  describe('updateContext method', () => {
    it('should return a promise', () => {
      expect(kalanfa.shim.updateContext()).toBeInstanceOf(Promise);
    });
  });

  describe('getContext method', () => {
    response = { node_id: 'abc', context: { test: 'test' } };
    beforeEach(function () {
      mockMessage = {
        data: {},
        event: 'context',
        nameSpace,
      };
      mockMediatorPromise = jest
        .spyOn(kalanfa.mediator, 'sendMessageAwaitReply')
        .mockResolvedValue(response);
    });
    it('should be called once', () => {
      kalanfa.shim.getContext();
      expect(mockMediatorPromise).toHaveBeenCalled();
    });
    it('should be called with the correct event, data, and namespace', () => {
      kalanfa.shim.getContext();
      expect(mockMediatorPromise).toHaveBeenCalledWith(mockMessage);
    });
    it('should return a promise that resolves to pagination object that contains an array of metadata objects', () => {
      return kalanfa.shim.getContext().then(data => {
        expect(data).toEqual(response);
      });
    });
  });

  describe.skip('version getter', () => {
    it('returns the correct version number', () => {
      // "testversion" is set in jest.conf. In production, this is injected by webpack.
      expect(kalanfa.shim.version).toEqual('testversion');
    });
  });

  describe('themeRenderer method', () => {
    it('sets the shim.theme object within the Shim class', async () => {
      const sendMessageAwaitReplySpy = jest
        .spyOn(kalanfa.mediator, 'sendMessageAwaitReply')
        .mockResolvedValue();
      await kalanfa.shim.themeRenderer({
        appBarColor: 'pink',
        textColor: 'blue',
      });
      expect(sendMessageAwaitReplySpy).toHaveBeenCalledWith({
        event: 'themechanged',
        nameSpace,
        data: {
          appBarColor: 'pink',
          textColor: 'blue',
        },
      });
    });
  });

  describe('searchContent method', () => {
    beforeEach(function () {
      mockMessage = {
        data: {},
        event: 'context',
        nameSpace,
      };
      mockMediatorPromise = jest
        .spyOn(kalanfa.mediator, 'sendMessageAwaitReply')
        .mockResolvedValue(response);
    });

    afterEach(() => {
      mockMediatorPromise.mockReset();
    });

    it('should be called with the correct event, data, and namespace', async () => {
      const options = {
        keyword: 'sewing',
        under: 'self',
        page: 1,
        pageSize: 25,
      };
      await kalanfa.shim.searchContent(options);
      expect(mockMediatorPromise).toHaveBeenCalledWith({
        event: 'datarequested',
        data: {
          options,
          dataType: 'SearchResult',
        },
        nameSpace,
      });
    });
  });
});
