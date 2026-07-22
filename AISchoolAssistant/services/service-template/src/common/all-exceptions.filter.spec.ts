import { BadRequestException, ArgumentsHost } from '@nestjs/common';
import { ForbiddenError } from '@asa/errors';
import { AllExceptionsFilter } from './all-exceptions.filter';

interface MockResponse {
  status: jest.Mock;
  type: jest.Mock;
  json: jest.Mock;
  headersSent: boolean;
}

function mockHost(response: MockResponse): ArgumentsHost {
  const request = { method: 'GET', originalUrl: '/api/v1/things' };
  return {
    switchToHttp: () => ({
      getResponse: () => response,
      getRequest: () => request,
    }),
  } as unknown as ArgumentsHost;
}

function newResponse(): MockResponse {
  const response = {
    headersSent: false,
  } as unknown as MockResponse;
  response.status = jest.fn().mockReturnValue(response);
  response.type = jest.fn().mockReturnValue(response);
  response.json = jest.fn().mockReturnValue(response);
  return response;
}

describe('AllExceptionsFilter', () => {
  let filter: AllExceptionsFilter;

  beforeEach(() => {
    filter = new AllExceptionsFilter();
  });

  it('renders a domain AppError as problem+json', () => {
    const res = newResponse();
    filter.catch(new ForbiddenError('nope'), mockHost(res));

    expect(res.status).toHaveBeenCalledWith(403);
    expect(res.type).toHaveBeenCalledWith('application/problem+json');
    const body = res.json.mock.calls[0][0];
    expect(body.status).toBe(403);
    expect(body.type).toBe('urn:asa:error:forbidden');
    expect(body.instance).toBe('/api/v1/things');
  });

  it('maps a Nest HttpException validation payload to errors[]', () => {
    const res = newResponse();
    const exception = new BadRequestException(['name must be a string']);
    filter.catch(exception, mockHost(res));

    expect(res.status).toHaveBeenCalledWith(400);
    const body = res.json.mock.calls[0][0];
    expect(body.status).toBe(400);
    expect(body.errors).toEqual([
      { field: '(body)', message: 'name must be a string' },
    ]);
  });

  it('maps an unknown error to an opaque 500', () => {
    const res = newResponse();
    filter.catch(new Error('boom'), mockHost(res));

    expect(res.status).toHaveBeenCalledWith(500);
    const body = res.json.mock.calls[0][0];
    expect(body.type).toBe('urn:asa:error:internal_error');
    expect(body.detail).toBe('An unexpected error occurred.');
  });

  it('does not write when headers are already sent', () => {
    const res = newResponse();
    res.headersSent = true;
    filter.catch(new Error('boom'), mockHost(res));
    expect(res.json).not.toHaveBeenCalled();
  });
});
