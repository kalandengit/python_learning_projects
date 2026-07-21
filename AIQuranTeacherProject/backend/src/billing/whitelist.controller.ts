import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  ParseUUIDPipe,
  Post,
  UseGuards,
} from '@nestjs/common';
import { ApiBearerAuth, ApiOperation, ApiTags } from '@nestjs/swagger';
import {
  AuthenticatedUser,
  CurrentUser,
} from '../common/decorators/current-user.decorator';
import { Roles } from '../common/decorators/roles.decorator';
import { RolesGuard } from '../common/guards/roles.guard';
import { UserRole } from '../users/user.entity';
import { BillingService, WhitelistEntry } from './billing.service';
import { GrantWhitelistDto } from './dto/grant-whitelist.dto';

/**
 * Admin-only management of the premium whitelist — users who receive free
 * premium access without paying, optionally for a defined period.
 */
@ApiTags('billing')
@ApiBearerAuth()
@Roles(UserRole.Admin)
@UseGuards(RolesGuard)
@Controller('billing/whitelist')
export class WhitelistController {
  constructor(private readonly billing: BillingService) {}

  @Get()
  @ApiOperation({ summary: 'List all whitelist grants (admin).' })
  list(): Promise<WhitelistEntry[]> {
    return this.billing.listWhitelist();
  }

  @Post()
  @ApiOperation({ summary: 'Grant a user free premium access (admin).' })
  grant(
    @CurrentUser() admin: AuthenticatedUser,
    @Body() dto: GrantWhitelistDto,
  ): Promise<WhitelistEntry> {
    return this.billing.grantWhitelist(
      dto.userId,
      dto.durationDays,
      dto.reason,
      admin.userId,
    );
  }

  @Delete(':userId')
  @ApiOperation({ summary: 'Revoke a user’s whitelist grant (admin).' })
  async revoke(
    @Param('userId', ParseUUIDPipe) userId: string,
  ): Promise<{ revoked: boolean }> {
    return { revoked: await this.billing.revokeWhitelist(userId) };
  }
}
