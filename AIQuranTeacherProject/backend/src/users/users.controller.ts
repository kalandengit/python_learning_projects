import {
  Body,
  Controller,
  Get,
  HttpCode,
  HttpStatus,
  NotFoundException,
  Post,
} from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import {
  AuthenticatedUser,
  CurrentUser,
} from '../common/decorators/current-user.decorator';
import { Public } from '../common/decorators/public.decorator';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';
import { AuthResult, PublicUser, UsersService } from './users.service';

@ApiTags('auth')
@Controller('auth')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Public()
  // Tighter limit on auth endpoints to blunt brute-force / credential stuffing.
  @Throttle({ default: { limit: 10, ttl: 60_000 } })
  @Post('register')
  @ApiOperation({
    summary: 'Create a new account and receive an access token.',
  })
  register(@Body() dto: RegisterDto): Promise<AuthResult> {
    return this.usersService.register(dto);
  }

  @Public()
  @Throttle({ default: { limit: 10, ttl: 60_000 } })
  @Post('login')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Exchange credentials for an access token.' })
  login(@Body() dto: LoginDto): Promise<AuthResult> {
    return this.usersService.login(dto);
  }

  @Get('me')
  @ApiOperation({ summary: 'Return the current authenticated user.' })
  async me(@CurrentUser() current: AuthenticatedUser): Promise<PublicUser> {
    const user = await this.usersService.findById(current.userId);
    if (!user) {
      throw new NotFoundException('User not found.');
    }
    return this.usersService.toPublic(user);
  }
}
