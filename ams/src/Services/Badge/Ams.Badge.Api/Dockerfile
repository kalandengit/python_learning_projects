# syntax=docker/dockerfile:1
# Multi-stage build: SDK builds, chiselled runtime runs as non-root (Section 12.1).
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY global.json Directory.Build.props ./
COPY BuildingBlocks/ BuildingBlocks/
COPY Services/Badge/ Services/Badge/
RUN dotnet publish Services/Badge/Ams.Badge.Api/Ams.Badge.Api.csproj \
    -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled AS runtime
WORKDIR /app
COPY --from=build /app/publish .
USER app
EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080
ENTRYPOINT ["dotnet", "Ams.Badge.Api.dll"]

# VERIFY: chiseled tag name for .NET 10 ("10.0-noble-chiseled") — confirm on mcr.microsoft.com.
